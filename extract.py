# Bultin Libraries
import csv
import glob
import logging
import sys
import os
import pickle
from typing import List, Optional, Dict
# Third-party
from z3 import *
from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
from antlr4.tree.Tree import TerminalNode
from neomodel import config
# Grammar generates by Antlr
from algorithms import flattenAlgorithmWithConditions
from condition_data_structure import Rule, LogicalExpression, AndExpression, LocalVariable, NotExpression, OrExpression, \
    ConstantExpression, ComparisonExpression
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from grammar.CMakeListener import CMakeListener
# Our own library
from datastructs import RefNode, TargetNode, Lookup, SelectNode, ConcatNode, \
    CustomCommandNode, TestNode, LiteralNode, Node, OptionNode, Directory, DirectoryNode, DefinitionNode
from analyze import printDefinitionsForATarget, printSourceFiles, printFilesForATarget, checkForCyclesAndPrint
from utils import util_handleConditions, util_getStringFromList,\
    util_create_and_add_refNode_for_variable, util_extract_variable_name
from commands import *


logging.basicConfig(filename='cmakeInspector.log', level=logging.DEBUG)
config.DATABASE_URL = 'bolt://neo4j:123@localhost:7687'

project_dir = "."

vmodel = VModel.getInstance()
lookupTable = Lookup.getInstance()
directoryTree = Directory.getInstance()
extension_type= "ECM"

no_op_commands=['cmake_policy','enable_testing','fltk_wrap_ui','install','mark_as_advanced','message','qt_wrap_cpp',
                'source_group','variable_watch','include_guard','install_icon']

                
find_package_lookup_directories=['cmake','CMake',':name',':name/cmake',':name/CMake','lib/cmake/:name',
                                 'share/cmake/:name','share/cmake-:version/:name','lib/:name','share/:name','lib/:name/cmake','lib/:name/CMake',
                                 'share/:name/cmake','share/:name/CMake',':name/lib/cmake/:name',
                                 ':name/share/cmake/:name',':name/lib/:name',':name/share/:name',
                                 ':name/lib/:name/cmake',':name/lib/:name/CMake',':name/share/:name/cmake',
                                 'share/:name/modules','bin','lib/x86_64-linux-gnu/cmake/:name'
                                 ':name/share/:name/CMake','lib/x86_64-linux-gnu/cmake/:name',
                                 '/opt/homebrew/Cellar/extra-cmake-modules/5.83.0/share/ECM/cmake',
                                 '/opt/homebrew/Cellar/extra-cmake-modules/5.83.0/share/ECM/modules',
                                 '/opt/homebrew/Cellar/extra-cmake-modules/5.83.0/share/ECM/kde-modules'
                                 '/opt/homebrew/Cellar/qt@5/5.15.2/bin',
                                 '/Applications/CMake.app/Contents/share/cmake-3.20/Modules',
                                 '/opt/homebrew/Cellar/cmake/3.20.4/share/cmake/Modules/',
                                 'share/cmake-:version/:name','share/cmake-:version/Modules',
                                 '/usr/share/kde4/apps/cmake/modules',
                                 '/opt/homebrew/Cellar/qt@5/5.15.2/lib/cmake/Qt5']
find_package_prefixes=['/usr','']
architecture='x86_64-linux-gnu'
includes_paths=['/Applications/CMake.app/Contents/share/cmake-3.20/Modules']
# Handle max recursion
currentFunction=None
prevFunction=[]
maxRecursionDepth=100
currentRecursionDepth=0
#
foreachCommandStack = []
foreachNodeStack = []
class CMakeExtractorListener(CMakeListener):
    rule: Optional[Rule] = None
    insideLoop = False;
    logicalExpressionStack: List[LogicalExpression] = []
    foreachVariable: List[String] = []

    def __init__(self):
        global vmodel
        global lookupTable
        global directoryTree
        vmodel = VModel.getInstance()
        lookupTable = Lookup.getInstance()
        directoryTree = Directory.getInstance()
        directoryTree.setRoot(project_dir)
        self.rule = None
        self.logicalExpressionStack = []

    def exitLogicalExpressionAnd(self, ctx:CMakeParser.LogicalExpressionAndContext):
        # Popping order matters
        rightLogicalExpression = self.logicalExpressionStack.pop()
        leftLogicalExpression = self.logicalExpressionStack.pop()
        andLogic = AndExpression(leftLogicalExpression, rightLogicalExpression)
        self.logicalExpressionStack.append(andLogic)

    def exitConstantValue(self, ctx:CMakeParser.ConstantValueContext):
        constant = ConstantExpression(ctx.getText())
        self.logicalExpressionStack.append(constant)

    def exitLogicalExpressionNot(self, ctx:CMakeParser.LogicalExpressionNotContext):
        logicalExpression = self.logicalExpressionStack.pop()
        notLogic = NotExpression(logicalExpression)
        self.logicalExpressionStack.append(notLogic)

    def exitLogicalExpressionOr(self, ctx:CMakeParser.LogicalExpressionOrContext):
        rightLogicalExpression = self.logicalExpressionStack.pop()
        leftLogicalExpression = self.logicalExpressionStack.pop()
        orLogic = OrExpression(leftLogicalExpression, rightLogicalExpression)
        self.logicalExpressionStack.append(orLogic)

    def exitLogicalEntity(self, ctx:CMakeParser.LogicalEntityContext):
        if len(ctx.getText()) and ctx.getText()[0]=="$":
            variableLookedUp = lookupTable.getKey(f'${ctx.getText()}')
        else:
            variableLookedUp = lookupTable.getKey(f'${{{ctx.getText()}}}')
        localVariable = LocalVariable(ctx.getText())
        if variableLookedUp:
            try:
                # Wherever we create a LocalVariable, we should flat the corresponding variable
                self.flattenVariableInConditionExpression(localVariable, variableLookedUp)
            except Z3Exception as e:
                logging.error("[exitLogicalEntity] {}".format(localVariable))
                raise e

        else:
            # We create an empty RefNode, perhaps it's a env variable
            variable_name = "${{{}}}".format(ctx.getText())
            variableNode = RefNode("{}".format(variable_name), None)
            lookupTable.setKey(variable_name, variableNode)
        self.logicalExpressionStack.append(localVariable)

    def exitIfStatement(self, ctx:CMakeParser.IfStatementContext):
        self.rule.setCondition(self.logicalExpressionStack.pop())
        assert len(self.logicalExpressionStack) == 0

    def exitComparisonExpression(self, ctx:CMakeParser.ComparisonExpressionContext):
        ctx_left_get_text: str = ctx.left.getText()
        ctx_right_get_text: str = ctx.right.getText()

        if ctx_left_get_text[0]=="$":
            leftVariableLookedUp = lookupTable.getKey(f'{ctx_left_get_text}')
        else:
            leftVariableLookedUp = lookupTable.getKey(f'${{{ctx_left_get_text}}}')

        if ctx_right_get_text[0]== "$":
            rightVariableLookedUp = lookupTable.getKey(f'{ctx_right_get_text}')
        else:
            rightVariableLookedUp = lookupTable.getKey(f'${{{ctx_right_get_text}}}')

        operator = ctx.operator.getText().upper()

        localVariableType = 'string' if operator in ('STRLESS', 'STREQUAL', 'STRGREATER', 'MATCHES',"VERSION_LESS",
                                                     "VERSION_GREATER","VERSION_GREATER_EQUAL","VERSION_EQUAL") else 'int'
        constantExpressionType = ConstantExpression.Z3_STR if operator in ('STRLESS', 'STREQUAL',
                                                                           'STRGREATER', 'MATCHES',"VERSION_LESS",
                                                                           "VERSION_GREATER","VERSION_GREATER_EQUAL" ,
                                                                           "VERSION_EQUAL") \
            else ConstantExpression.PYTHON_STR

        if leftVariableLookedUp:
            leftExpression = LocalVariable(ctx_left_get_text, localVariableType)
            self.flattenVariableInConditionExpression(leftExpression, leftVariableLookedUp)
        else:
            realVar = ctx_left_get_text.strip('"').lstrip('${').rstrip('}')
            if realVar.upper().startswith('CMAKE_') or realVar.upper().startswith('${CMAKE_'):
                # Reserved variable for CMake
                variable_name = "${{{}}}".format(realVar)
                variableNode = RefNode("{}".format(variable_name), None)
                lookupTable.setKey(variable_name, variableNode)
                leftExpression = LocalVariable(realVar, localVariableType)
            else:
                leftExpression = ConstantExpression(realVar, constantExpressionType)

        if rightVariableLookedUp:
            rightExpression = LocalVariable(ctx_right_get_text, localVariableType)
            self.flattenVariableInConditionExpression(rightExpression, rightVariableLookedUp)
        else:
            realVar = ctx_right_get_text.strip('"').lstrip('${').rstrip('}')
            if realVar.upper().startswith('CMAKE_'):
                # Reserved variable for CMake
                variable_name = "${{{}}}".format(realVar)
                variableNode = RefNode("{}".format(variable_name), None)
                lookupTable.setKey(variable_name, variableNode)
                rightExpression = LocalVariable(realVar, localVariableType)
            else:
                rightExpression = ConstantExpression(realVar, constantExpressionType)

        self.logicalExpressionStack.append(
            ComparisonExpression(leftExpression, rightExpression, operator)
        )

    def flattenVariableInConditionExpression(self, expression: LocalVariable, variable: Node):
        # Flattening the variable used inside the condition, like [(True, {bar}), (False, {Not bar, john > 2})]
        flattened = flattenAlgorithmWithConditions(variable, ignoreSymbols=True) or []
        # We need to add an assertion to the solver, like {bar, foo == True} and {Not bar, john > 2, foo == False}
        temp_result = []
        for item in flattened:
            for condition in self.rule.flattenedResult:
                s = Solver()
                if isinstance(expression.getAssertions(), SeqRef):
                    assertion = condition.union(item[1].union({expression.getAssertions() == StringVal(item[0])}))
                else:
                    try:
                        rightHandSide = item[0]
                        if isinstance(expression.getAssertions(), BoolRef):
                            # To convert float (3.14) to (314) and also support ("3.14")
                            if item[0].replace('.','', 1).replace('"', '').isdigit():
                                rightHandSide = bool(int(item[0].replace('.','', 1).replace('"', '')))

                            if rightHandSide == '""':
                                rightHandSide = False
                            elif not isinstance(rightHandSide, bool):
                                # TODO: needs more investigation, I think we are missing some problems
                                # Like 'INSTALL_DEFAULT_BASEDIR' in ET: Legacy project
                                rightHandSide = bool(rightHandSide)

                        if isinstance(expression.getAssertions(), ArithRef) and isinstance(rightHandSide, str):
                            cleanedRighthandSide = item[0].replace('.','', 1).replace('"', '')
                            if(cleanedRighthandSide.isdigit()):
                                rightHandSide = int(cleanedRighthandSide)
                            else:
                                rightHandSide = Int(cleanedRighthandSide)
                        assertion = condition.union(item[1].union({expression.getAssertions() == rightHandSide}))
                    except Exception as e:
                        print(f"Variable name: {expression.variableName} and item[0]: {item[0]}")
                        raise e
                s.add(assertion)
                if s.check() == sat:
                    temp_result.append(assertion)
        if not temp_result:
            temp_result.append(set())
        self.rule.flattenedResult = temp_result

    def exitElseIfStatement(self, ctx:CMakeParser.ElseIfStatementContext):
        # Logical expression for the elseif itself
        rightLogic = self.logicalExpressionStack.pop()

        # For the else if, to be evaluated as true, all the previous conditions should be evaluated as false
        # Using bellow algorithm, we need to check the latest condition only.
        logic, prevConditionFlattened = util_getNegativeOfPrevLogics()

        andLogic = AndExpression(logic, rightLogic)
        assert len(self.logicalExpressionStack) == 0
        self.rule.setCondition(andLogic)
        self.rule.flattenedResult = list(prevConditionFlattened)
        vmodel.pushSystemState(self.rule)

    def enterIfCommand(self, ctx: CMakeParser.IfCommandContext):
        # Make sure that the logical expression stack is empty every time we enter an if statement
        assert len(self.logicalExpressionStack) == 0
        self.rule = Rule()

        vmodel.setInsideIf()
        vmodel.pushCurrentLookupTable()
        vmodel.ifLevel += 1

        self.rule.setType('if')
        self.rule.setLevel(vmodel.ifLevel)
        vmodel.pushSystemState(self.rule)

    def enterElseIfStatement(self, ctx: CMakeParser.ElseIfStatementContext):
        # Make sure that the logical expression stack is empty every time we enter an else if statement
        assert len(self.logicalExpressionStack) == 0
        self.rule = Rule()

        vmodel.popLookupTable()
        vmodel.pushCurrentLookupTable()

        self.rule.setType('elseif')
        self.rule.setLevel(vmodel.ifLevel)

    def enterElseStatement(self, ctx: CMakeParser.ElseStatementContext):
        # Make sure that the logical expression stack is empty every time we enter an else statement
        assert len(self.logicalExpressionStack) == 0
        self.rule = Rule()

        # Else statement is true when all the previous conditions are false
        # Same as elseif, we only need to check the previous state
        logic, prevConditionFlattened = util_getNegativeOfPrevLogics()

        while True:
            systemStateObject = vmodel.getCurrentSystemState()
            state = systemStateObject.getType()
            if state != 'if':
                vmodel.popSystemState()
            else:
                break

        vmodel.popLookupTable()
        vmodel.pushCurrentLookupTable()

        self.rule.setType('elseif')
        self.rule.setLevel(vmodel.ifLevel)
        self.rule.setCondition(logic)
        self.rule.flattenedResult = list(prevConditionFlattened)
        vmodel.pushSystemState(self.rule)

    def exitIfCommand(self, ctx: CMakeParser.IfCommandContext):
        vmodel.setOutsideIf()
        vmodel.popLookupTable()
        vmodel.ifLevel -= 1
        # In case of an if statement without else command, the state of the if itself and multiple else ifs
        # still exists. We should keep popping until we reach to the if
        while True:
            systemStateObject = vmodel.popSystemState()
            state = systemStateObject.type
            if state == 'if':
                break

    def enterOptionCommand(self, ctx: CMakeParser.OptionCommandContext):
        arguments = [child.getText() for child in ctx.argument().getChildren() if not isinstance(child, TerminalNode)]
        optionName = arguments.pop(0)
        optionInitialValue = False
        if len(arguments) > 1:
            arguments.pop(0)  # Remove description from the option command
            optionInitialValue = arguments.pop(0)
        vmodel.addOption(optionName, optionInitialValue)
        optionNode = OptionNode(optionName)
        optionNode.default = optionInitialValue
        util_create_and_add_refNode_for_variable(optionName, optionNode)




    def exitForeachOptions(self,ctx:CMakeParser.WhileCommandContext):
        ctx.left.getText()
        self.foreachVariable.append()
    def enterForeachCommand(self, ctx:CMakeParser.WhileCommandContext):
        assert len(self.foreachVariable) == 0
        self.insideLoop = True


    def enterForeachInputs(self, ctx:CMakeParser.WhileStatementContext):
        global foreachCommandStack
        ctx_var = ctx.getText();
        if ctx_var[0] == "$":
            foreachVariableRawName = f'{ctx_var}'
        else:
            foreachVariableRawName = f'${{{ctx_var}}}'

        foreachCommandStack.append(foreachVariableRawName)

    def exitForeachStatement(self, ctx:CMakeParser.WhileStatementContext):
        global foreachCommandStack,foreachNodeStack

        # # self.rule.setType('foreach')
        # assert len(self.logicalExpressionStack) == 0
        # foreachCommand(self.rule)
        foreachNodeStack.append(foreachCommandStack)
        foreachCommandStack =[]
        foreachCommand();



    def exitForeachCommand(self, ctx:CMakeParser.WhileCommandContext):
        global foreachCommandStack
        endForeachCommand(foreachNodeStack.pop())
        self.insideLoop = False




    def enterWhileCommand(self, ctx:CMakeParser.WhileCommandContext):
        assert len(self.logicalExpressionStack) == 0
        self.rule = Rule()
        self.rule.setType('while')

    def exitWhileStatement(self, ctx:CMakeParser.WhileStatementContext):
        self.rule.setCondition(self.logicalExpressionStack.pop())
        assert len(self.logicalExpressionStack) == 0
        whileCommand(self.rule)

    def exitWhileCommand(self, ctx:CMakeParser.WhileCommandContext):
        endwhileCommand()

    def enterFunctionCommand(self, ctx:CMakeParser.FunctionCommandContext):
        startIdx = ctx.functionBody().start.start
        endIdx = ctx.functionBody().stop.stop
        inputStream = ctx.start.getInputStream()
        bodyText = inputStream.getText(startIdx, endIdx)
        isMacro = ctx.functionStatement().children[0].getText().lower() == 'macro'

        arguments = [child.getText() for child in ctx.functionStatement().argument().getChildren() if
                     not isinstance(child, TerminalNode)]
        functionName = arguments.pop(0)
        vmodel.functions[functionName] = {'arguments': arguments, 'commands': bodyText, 'isMacro': isMacro}


    def includeCommand(self,arguments):
        commandNode = CustomCommandNode("include")
        if 'RESULT_VARIABLE' in arguments:
            varIndex = arguments.index('RESULT_VARIABLE')
            arguments.pop(varIndex)  # This is RESULT_VAR
            util_create_and_add_refNode_for_variable(arguments.pop(varIndex), commandNode,
                                                     relatedProperty='RESULT_VARIABLE')

        args = vmodel.expand(arguments)
        include_possibilities=flattenAlgorithmWithConditions(args)
        commandNode.depends.append(args)
        if self.insideLoop:
            print("[warning] include inside loop neglected")
            return;

        currentPath = flattenAlgorithmWithConditions(vmodel.expand(['${CMAKE_CURRENT_LIST_DIR}']))
        if len(currentPath):
            currentPath = currentPath[0][0];
        else:
            currentPath = '';

        for include_possibility in include_possibilities:
            argsVal = include_possibility[0]
            includedFile = os.path.join(project_dir, argsVal)

            # clean the include path
            while includedFile.find('//') != -1:
                includedFile = includedFile.replace('//','/')


            # We execute the command if we can find the CMake file and there is no condition to execute it
            if os.path.isfile(includedFile):
                parseFile(includedFile,True)

                # for item in vmodel.nodes:
                #     if item not in prevNodeStack:
                #         commandNode.commands.append(item)
            elif os.path.isdir(includedFile):
                util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_DIR',
                                                         LiteralNode(f"include_{includedFile}", includedFile))
                parseFile(os.path.join(includedFile, 'CMakeLists.txt'),True)

            else:
                cmake_module_paths = flattenAlgorithmWithConditions(vmodel.expand(["${CMAKE_MODULE_PATH}"]))
                for cmake_module_path in cmake_module_paths:
                    if os.path.exists(os.path.join(cmake_module_path[0], f'{argsVal}.cmake').replace('//','/')):
                        includePath = os.path.join(cmake_module_path[0], f'{argsVal}.cmake').replace('//','/')
                        if os.path.isfile(includePath):
                            pathDir =  os.path.dirname(includePath)
                            util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_DIR',
                                                                     LiteralNode(f"include_{includedFile}", pathDir));
                            parseFile(includePath, True)
                            break
                    # assert len(cmake_module_path[1]) == 0 # check if we have multiple conditions
                    if not(len(cmake_module_path[1]) == 0):
                        logging.warning('Something might go wrong, conditional module path exist!')
                else:
                    paths = [os.path.join(path,argsVal).replace('//','/')+'.cmake' for path in includes_paths]
                    paths += [os.path.join(path,argsVal).replace('//','/') for path in includes_paths]
                    foundModule = False
                    for path in paths:
                        if os.path.isfile(path):
                            pathDir =  os.path.dirname(path)
                            util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_DIR',
                                                                     LiteralNode(f"include_{includedFile}", pathDir));
                            parseFile(path, True)
                            foundModule = True
                    if not foundModule:
                        print("[error][enterCommand_invocation] Cannot Find : {} to include, conditions {}".format(arguments,include_possibility[1]))
                        vmodel.nodes.append(util_handleConditions(commandNode, commandNode.getName()))
                    # now we turn the current list dir back
                    util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR',
                                                             LiteralNode(f"parse_{currentPath}", currentPath))
                    util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_DIR',
                                                             LiteralNode(f"original_{currentPath}", currentPath))
            # now we turn the current list dir back
            util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR',
                                                     LiteralNode(f"parse_{currentPath}", currentPath))
            util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_DIR',
                                                     LiteralNode(f"original_{currentPath}", currentPath))


    def find_Module(self,packageName,findPackageNode):
        global vmodel
        global project_dir

        flattened_packageName = flattenAlgorithmWithConditions(packageName)
        for possible_include in flattened_packageName:
            includePath = None
            # First we check CMAKE_MODULE_PATH
            cmake_module_paths = flattenAlgorithmWithConditions(vmodel.expand(["${CMAKE_MODULE_PATH}"]))
            for cmake_module_path in cmake_module_paths:
                if os.path.exists(os.path.join(cmake_module_path[0], f'Find{possible_include[0]}.cmake')):
                    includePath = os.path.abspath(os.path.join(cmake_module_path[0], f'Find{possible_include[0]}.cmake'))
                    break
                if not (len(cmake_module_path[1]) == 0 and len(possible_include[1]) == 0):
                    print("something might go wrong, conditional module path exist!")
                # assert len(cmake_module_path[1]) == 0 and len(possible_include[1]) == 0 # check if we have multiple conditions
            else:
                # If not found, then, we search in default directories
                for find_package_prefix in find_package_prefixes:
                    for index, path in enumerate(find_package_lookup_directories):
                        if os.path.exists(os.path.join(find_package_prefix, path.replace(':name', possible_include[0]),
                                                       f'Find{possible_include[0]}.cmake')):
                            includePath = os.path.abspath(os.path.join(find_package_prefix, path.replace(':name', possible_include[0]),
                                                       f'Find{possible_include[0]}.cmake'))
                            break
                    if includePath:
                        break
            if includePath:
                util_create_and_add_refNode_for_variable(packageName.getValue() + "_Module",
                                                         LiteralNode(includePath, includePath))
                util_create_and_add_refNode_for_variable('PACKAGE_FIND_NAME',
                                                         LiteralNode(f"name_{packageName.getValue()}",
                                                                     packageName.getValue()))

                util_create_and_add_refNode_for_variable('PACKAGE_FIND_VERSION',
                                                         LiteralNode('VERSION_MINOR', 20))

                if len(possible_include[1]):
                    vmodel = VModel.getInstance()

                    prior_condition = possible_include[1]
                    logicalExpression = DummyExpression(prior_condition)
                    rule = Rule()
                    if len(vmodel.systemState):
                        rule.setLevel(vmodel.systemState[-1].level)
                    else:
                        rule.setLevel(1)
                    rule.setType('if')
                    rule.setCondition(logicalExpression)
                    vmodel.pushSystemState(rule)
                    vmodel.pushCurrentLookupTable()
                    vmodel.nodeStack.append(list(vmodel.nodes))

                    tempProjectDir = project_dir
                    project_dir = os.path.dirname(includePath)
                    setCommand(['CMAKE_CURRENT_LIST_DIR', project_dir])
                    self.includeCommand([includePath])
                    project_dir = tempProjectDir

                    rule = vmodel.popSystemState()
                    prevNodeStack = vmodel.nodeStack.pop()
                    for item in vmodel.nodes:
                        if item not in prevNodeStack:
                            findPackageNode.pointTo.append(item)

                else:
                    tempProjectDir = project_dir
                    project_dir = os.path.dirname(includePath)
                    setCommand(['CMAKE_CURRENT_LIST_DIR', project_dir])
                    self.includeCommand([includePath])
                    project_dir = tempProjectDir
                return True
        return False

    def enterCommand_invocation(self, ctx: CMakeParser.Command_invocationContext):
        global project_dir
        global extension_type
        global vmodel
        global lookupTable

        commandId = ctx.Identifier().getText().lower()
        arguments = [child.getText() for child in ctx.argument().getChildren() if not isinstance(child, TerminalNode)]

        # a hacky fix for consecutive double quotes
        regex = r"^\"\"(.*?)\"\"$"
        for idx, argument in enumerate(arguments):
            arguments[idx] = argument.replace(regex,"")


        if vmodel.currentFunctionCommand is not None and commandId not in ('endfunction', 'endmacro'):
            vmodel.currentFunctionCommand.append((commandId, arguments))
            return

        if commandId == 'set':
            if vmodel.currentFunctionCommand is not None:
                vmodel.currentFunctionCommand.append(('set', arguments))
            else:
                setCommand(arguments)

        # add_definitions(-DFOO -DBAR ...)
        elif commandId == 'add_definitions':
            handleCompileDefinitionCommand(arguments, command='add', specific=False, project_dir=project_dir)

        # remove_definitions(-DFOO -DBAR ...)
        elif commandId == 'remove_definitions':
            handleCompileDefinitionCommand(arguments, command='remove', specific=False, project_dir=project_dir)

        # load_cache(pathToCacheFile READ_WITH_PREFIX
        #    prefix entry1...)
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # load_cache(pathToCacheFile [EXCLUDE entry1...]
        #    [INCLUDE_INTERNALS entry1...])
        elif commandId == 'load_cache':
            cacheNode = CustomCommandNode('load_cache_{}'.format(vmodel.getNextCounter()))

            if 'READ_WITH_PREFIX' in arguments:
                argIndex = arguments.index('READ_WITH_PREFIX')
                arguments.pop(argIndex)  # This is always 'READ_WITH_PREFIX'
                prefix = arguments.pop(argIndex)
                while len(arguments) > argIndex:
                    varname = arguments.pop(argIndex)
                    util_create_and_add_refNode_for_variable("{}{}".format(prefix, varname), cacheNode)

            cacheNode.commands.append(vmodel.expand(arguments))
        # find_library (<VAR> name1 [path1 path2 ...])
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++
        # find_path (<VAR> name1 [path1 path2 ...])
        elif commandId in ('find_library', 'find_path', 'find_program'):
            varFound = arguments.pop(0)
            varNotFound = varFound + '-NOTFOUND'
            findLibraryNode = CustomCommandNode("{}_{}".format(commandId, vmodel.getNextCounter()))
            findLibraryNode.commands.append(vmodel.expand(arguments))
            util_create_and_add_refNode_for_variable(varFound, findLibraryNode, relatedProperty='FOUND')
            util_create_and_add_refNode_for_variable(varNotFound, findLibraryNode, relatedProperty='NOTFOUND')

        # find_package( < package > [version][EXACT][QUIET][MODULE]
        #                 [REQUIRED][[COMPONENTS][components...]]
        #                 [OPTIONAL_COMPONENTS
        #                 components...]
        #                 [NO_POLICY_SCOPE])
        elif commandId == 'find_package':
            # XXX versioning is not considered in this version
            packageName = vmodel.expand([arguments[0]])
            findPackageNode = CustomCommandNode("find_package_{}".format(vmodel.getNextCounter()))
            findPackageNode.commands.append(vmodel.expand(arguments))
            util_create_and_add_refNode_for_variable(packageName.getValue() + "_FOUND", findPackageNode)

            capitalArguments = [x.upper() for x in arguments]
            if 'REQUIRED' in capitalArguments:
                requiredIndex = capitalArguments.index('REQUIRED')
            else:
                requiredIndex = -1
            isModule = False
            if 'MODULE' in capitalArguments:
                isModule = True

            requiredPackage = False
            if requiredIndex != -1:
                requiredPackage = True


            flattened_packageName = flattenAlgorithmWithConditions(packageName)
            version=''
            if self.find_Module(packageName,findPackageNode):
                return True;
            elif not isModule:
                for possible_include in flattened_packageName:
                    includePath = None
                    # First we check CMAKE_MODULE_PATH
                    cmake_module_paths = flattenAlgorithmWithConditions(vmodel.expand(["${CMAKE_MODULE_PATH}"]))
                    for cmake_module_path in cmake_module_paths:
                        if os.path.exists(os.path.join(cmake_module_path[0],f'{possible_include[0]}Config.cmake')):
                            includePath = os.path.join(cmake_module_path[0],f'{possible_include[0]}Config.cmake')
                            version = os.path.join(cmake_module_path[0],f'{possible_include[0]}ConfigVersion.cmake')
                            break
                        if os.path.exists(os.path.join(cmake_module_path[0], f'{possible_include[0]}-config.cmake')):
                            includePath = os.path.exists(
                                os.path.join(cmake_module_path[0], f'{possible_include[0]}-config.cmake'))
                            version = os.path.join(cmake_module_path[0],f'{possible_include[0]}-config-version.cmake')

                            break
                        if not(len(cmake_module_path[1]) == 0 and len(possible_include[1]) == 0):
                            print("something might go wrong, conditional module path exist!")
                        # assert len(cmake_module_path[1]) == 0 and len(possible_include[1]) == 0 # check if we have multiple conditions
                    else:
                        # If not found, then, we search in default directories
                        for find_package_prefix in find_package_prefixes:
                            for index,path in enumerate(find_package_lookup_directories):
                                if os.path.exists(os.path.join(find_package_prefix,path.replace(':name',possible_include[0]),f'{possible_include[0]}Config.cmake')):
                                    includePath = os.path.join(find_package_prefix,path.replace(':name',possible_include[0]),f'{possible_include[0]}Config.cmake')
                                    version = os.path.join(find_package_prefix,path.replace(':name',possible_include[0]),f'{possible_include[0]}ConfigVersion.cmake')
                                    break

                                if os.path.exists(os.path.join(find_package_prefix,path.replace(':name',possible_include[0]),f'{possible_include[0].lower()}-config.cmake')):
                                    includePath = os.path.join(find_package_prefix,path.replace(':name',possible_include[0]),f'{possible_include[0].lower()}-config.cmake')
                                    version = os.path.join(find_package_prefix,path.replace(':name',possible_include[0]),f'{possible_include[0].lower()}-config-version.cmake')
                                    break
                            if includePath:
                                break
                    if includePath:
                        util_create_and_add_refNode_for_variable(packageName.getValue() + "_CONFIG", LiteralNode(includePath, includePath))
                        util_create_and_add_refNode_for_variable('PACKAGE_FIND_NAME',
                                                                 LiteralNode(f"name_{packageName.getValue()}", packageName.getValue()))
                        if len(possible_include[1]):
                            vmodel = VModel.getInstance()

                            prior_condition = possible_include[1]
                            logicalExpression = DummyExpression(prior_condition)
                            rule = Rule()
                            if len(vmodel.systemState):
                                rule.setLevel(vmodel.systemState[-1].level)
                            else:
                                rule.setLevel(1)
                            rule.setType('if')
                            rule.setCondition(logicalExpression)
                            vmodel.pushSystemState(rule)
                            vmodel.pushCurrentLookupTable()
                            vmodel.nodeStack.append(list(vmodel.nodes))

                            tempProjectDir = project_dir
                            project_dir = os.path.dirname(includePath)
                            # load_version
                            if(os.path.exists(version)):
                                self.includeCommand([version])
                                package_version = flattenAlgorithmWithConditions(vmodel.expand(['PACKAGE_VERSION']))
                                if len(package_version):
                                    setCommand([f"{packageName.getValue()}_FIND_VERSION",package_version[0][0]]);
                            # end load version
                            setCommand(['CMAKE_CURRENT_LIST_DIR', project_dir])
                            self.includeCommand([includePath])
                            project_dir = tempProjectDir

                            rule = vmodel.popSystemState()
                            prevNodeStack = vmodel.nodeStack.pop()
                            for item in vmodel.nodes:
                                if item not in prevNodeStack:
                                    findPackageNode.pointTo.append(item)

                        else:
                            tempProjectDir = project_dir
                            project_dir = os.path.dirname(includePath)
                            # load_version
                            if(os.path.exists(version)):
                                self.includeCommand([version])
                                package_version = flattenAlgorithmWithConditions(vmodel.expand(['PACKAGE_VERSION']))
                                if len(package_version):
                                    setCommand([f"{packageName.getValue()}_FIND_VERSION",package_version[0][0]]);
                            # end load version

                            setCommand(['CMAKE_CURRENT_LIST_DIR',project_dir])
                            self.includeCommand([includePath])
                            project_dir = tempProjectDir

                    elif requiredPackage:
                        logging.error("Required package not found: {}".format(packageName.getValue()))
                        # raise Exception("Required package not found: {}".format(packageName.getValue()))
                        print("[Bug or Error]Required package not found: {}".format(packageName.getValue()))
            elif requiredPackage:
                logging.error("Required module not found: {}".format(packageName.getValue()))
                raise Exception("Required package not found: {}".format(packageName.getValue()))
                # print("Required module not found: {}".format(packageName.getValue()))

            # capitalArguments = [x.upper() for x in arguments]
            # projectVersion = None
            # projectDescription = None
            # if 'DESCRIPTION' in capitalArguments:
            #     descriptionIndex = arguments.index('DESCRIPTION')
            #     projectDescription = arguments[descriptionIndex+1]


        # include( < file | module > [OPTIONAL][RESULT_VARIABLE < VAR >]
        #          [NO_POLICY_SCOPE])
        elif commandId in ('include'):
            self.includeCommand(arguments)

        elif commandId == 'find_file':
            variableName = arguments.pop(0)
            fileNode = CustomCommandNode('find_file_{}'.format(vmodel.getNextCounter()))
            fileNode.pointTo.append(vmodel.expand(arguments))
            foundRefNode = RefNode("{}_{}".format(variableName, vmodel.getNextCounter()), fileNode)
            notFoundRefNode = RefNode("{}-NOTFOUND_{}".format(variableName, vmodel.getNextCounter()), fileNode)

            lookupTable.setKey("${{{}}}".format(variableName), foundRefNode)
            lookupTable.setKey("${{{}}}".format(variableName + "-NOTFOUND"), notFoundRefNode)
            vmodel.nodes.append(foundRefNode)
            vmodel.nodes.append(notFoundRefNode)

        elif commandId == 'math':
            # Throw first argument away, it is always "EXPR" according to the document
            arguments.pop(0)
            varName = arguments.pop(0)
            mathNode = CustomCommandNode("{}_{}".format('MATH', vmodel.getNextCounter()))
            mathNode.pointTo.append(vmodel.expand(arguments))
            refNode = RefNode("{}_{}".format(varName, vmodel.getNextCounter()), mathNode)
            lookupTable.setKey("${{{}}}".format(varName), refNode)
            vmodel.nodes.append(refNode)

        # TODO: We should keep the outputs in lookup table
        #       We cannot handle scenario given in : https://gist.github.com/socantre/7ee63133a0a3a08f3990
        #       This is a very common use of this command, but we don't have solution for that
        # add_custom_command(OUTPUT output1 [output2 ...]
        #        COMMAND command1 [ARGS] [args1...]
        #        [COMMAND command2 [ARGS] [args2...] ...]
        #        [MAIN_DEPENDENCY depend]
        #        [DEPENDS [depends...]]
        #        [IMPLICIT_DEPENDS <lang1> depend1
        #                         [<lang2> depend2] ...]
        #        [WORKING_DIRECTORY dir]
        #        [COMMENT comment] [VERBATIM] [APPEND])
        # -----------------------------------------------------
        # add_custom_command(TARGET target
        #            PRE_BUILD | PRE_LINK | POST_BUILD
        #            COMMAND command1 [ARGS] [args1...]
        #            [COMMAND command2 [ARGS] [args2...] ...]
        #            [WORKING_DIRECTORY dir]
        #            [COMMENT comment] [VERBATIM])
        elif commandId == 'add_custom_command':
            OPTIONS = ['OUTPUT', 'COMMAND', 'MAIN_DEPENDENCY', 'DEPENDS', 'IMPLICIT_DEPENDS',
                       'WORKING_DIRECTORY', 'COMMENT', 'VERBATIM', 'APPEND']
            customCommand = CustomCommandNode("custom_command")
            depends = []
            commandSig = arguments.pop(0)
            if commandSig == 'TARGET':
                targetName = arguments.pop(0)
                target = lookupTable.getKey("t:{}".format(targetName))
                commandType = arguments.pop(0)
                if commandType == 'POST_BUILD':
                    depends.append(targetName)
                    vmodel.nodes.append(customCommand)
                else:
                    target.addLinkLibrary(customCommand)
            else:
                while arguments[0] not in OPTIONS:
                    outName = arguments.pop(0)
                    if lookupTable.getKey(outName):
                        variable = lookupTable.getKey(outName)
                        if isinstance(variable.getPointTo(), ConcatNode):
                            variable.pointTo.addToBeginning(customCommand)
                        else:
                            variable.pointTo = customCommand
                    else:
                        refNode = RefNode(outName, customCommand)
                        vmodel.nodes.append(refNode)

            while 'COMMAND' in arguments:
                # From that index until the next command we parse the commands
                commands = []
                commandStartingIndex = arguments.index('COMMAND')
                # pop 'COMMAND'
                arguments.pop(commandStartingIndex)
                while len(arguments) > commandStartingIndex and arguments[commandStartingIndex] not in OPTIONS:
                    commands.append(arguments.pop(commandStartingIndex))
                customCommand.commands.append(vmodel.expand(commands))

            if 'MAIN_DEPENDENCY' in arguments:
                mdIndex = arguments.index('MAIN_DEPENDENCY')
                # pop 'MAIN_DEPENDENCY'
                arguments.pop(mdIndex)
                depends.append(arguments.pop(mdIndex))

            if 'DEPENDS' in arguments:
                dIndex = arguments.index('DEPENDS')
                # pop 'DEPENDS'
                arguments.pop(dIndex)
                while len(arguments) > dIndex and arguments[dIndex] not in OPTIONS:
                    depends.append(arguments.pop(dIndex))

            if depends:
                customCommand.depends.append(vmodel.expand(depends))

        # add_test(NAME <name> COMMAND <command> [<arg>...]
        #  [CONFIGURATIONS <config>...]
        #  [WORKING_DIRECTORY <dir>])
        # --------------------------------------------------
        # add_test(<name> <command> [<arg>...])
        elif commandId == 'add_test':
            # Check if we should proceed with first signature or the second one
            if arguments[0] == 'NAME':
                arguments.pop(0)  # NAME
                testName = arguments.pop(0)
                testNode = TestNode(testName)
                arguments.pop(0)  # COMMAND

                if 'CONFIGURATIONS' in arguments:
                    cIndex = arguments.index('CONFIGURATIONS')
                    arguments.pop(cIndex)  # 'CONFIGURATIONS'
                    configArgs = []
                    while cIndex < len(arguments) and arguments[cIndex] not in ['COMMAND', 'WORKING_DIRECTORY']:
                        configArgs.append(arguments.pop(cIndex))
                    testNode.configurations = vmodel.expand(configArgs)

                if 'WORKING_DIRECTORY' in arguments:
                    wdIndex = arguments.index('WORKING_DIRECTORY')
                    arguments.pop(wdIndex)  # WORKING_DIRECTORY
                    testNode.working_directory = vmodel.expand([arguments.pop(wdIndex)])

                testNode.command = vmodel.expand(arguments)
            else:
                # We go with the second sig
                testName = arguments.pop(0)
                testNode = TestNode(testName)
                testNode.command = vmodel.expand(arguments)

            vmodel.nodes.append(testNode)

        # cmake_host_system_information(RESULT <variable> QUERY <key> ...)
        elif commandId == 'cmake_host_system_information':
            arguments.pop(0)  # First argument is RESULT
            variableName = arguments.pop(0)
            arguments.pop(0)  # This one is always QUERY
            commandNode = CustomCommandNode("cmake_host_system_information_{}".format(vmodel.getNextCounter()))
            commandNode.commands.append(vmodel.expand(arguments))
            refNode = RefNode("{}_{}".format(variableName, vmodel.getNextCounter()), commandNode)
            lookupTable.setKey("${{{}}}".format(variableName), refNode)
            vmodel.nodes.append(refNode)

        # TODO: It may be a good idea to list commands and files under a different list
        #       We should create a new class for this command to separate command and sources and etc ...
        #       This new class should inherit TargetNode
        elif commandId == 'add_custom_target':
            targetName = arguments.pop(0)
            dependedElement: List[TargetNode] = []
            defaultBuildTarget = False
            # Check for some keywords in the command
            if 'ALL' in arguments:
                allIndex = arguments.index('ALL')
                arguments.pop(allIndex)
                defaultBuildTarget = True
            # Check if we have depend command
            if 'DEPENDS' in arguments:
                dependsIndex = arguments.index('DEPENDS')
                # Trying to find the next argument after DEPENDS. Anything in between is the one that this command
                # should depends on
                nextArgIndex = len(arguments)
                for otherArg in ['ALL', 'COMMAND', 'WORKING_DIRECTORY', 'COMMENT', 'VERBATIM', 'SOURCES']:
                    if otherArg not in arguments:
                        continue
                    otherArgIndex = arguments.index(otherArg)
                    if otherArgIndex > dependsIndex:
                        nextArgIndex = min(nextArgIndex, otherArgIndex)

                for i in range(dependsIndex + 1, nextArgIndex):
                    # TODO: There is a bug here. As we add a number to the end of nodes, vmodel.findNode may not be
                    #       be able to find the node based on name
                    targetElement = lookupTable.getKey("t:{}".format(arguments[i])) \
                                    or vmodel.findNode(arguments[i])
                    if targetElement is None:
                        targetElement = RefNode(arguments[i], None)
                        lookupTable.setKey(arguments[i], targetElement)
                        # raise Exception("There is a problem in finding dependency for {}".format(targetName))
                    dependedElement.append(targetElement)

                # Now we have to pop these arguments:
                for i in range(dependsIndex, nextArgIndex):
                    arguments.pop(dependsIndex)

            targetNode = TargetNode("{}".format(targetName), vmodel.expand(arguments))
            targetNode.isCustomTarget = True
            targetNode.defaultBuildTarget = defaultBuildTarget
            targetNode.sources.listOfNodes += dependedElement
            lookupTable.setKey("t:{}".format(targetName), targetNode)
            vmodel.nodes.append(targetNode)

        # get_filename_component(<var> <FileName> <mode> [CACHE])
        # -------------------------------------------------------
        # get_filename_component(<var> <FileName> <mode> [BASE_DIR <dir>] [CACHE])
        # -------------------------------------------------------
        # get_filename_component(<var> <FileName> PROGRAM [PROGRAM_ARGS <arg_var>] [CACHE])
        # TODO: WE do not support ABSOLUTE at this point
        elif commandId == 'get_filename_component':
            varName = arguments.pop(0)

            # currentPath = flattenAlgorithmWithConditions(vmodel.expand(['${CMAKE_CURRENT_LIST_DIR}']))
            # if len(currentPath):
            #     currentPath = currentPath[0][0];
            # else:
            #     currentPath = '';

            commandNode = CustomCommandNode("get_filename_component_{}".format(vmodel.getNextCounter()))
            otherArgs = vmodel.expand(arguments)
            commandNode.commands.append(otherArgs)

            pathVariable = vmodel.expand([arguments[0]])
            tmp = flattenAlgorithmWithConditions(pathVariable)
            # TODO: We need to support multiple file conditions here!
            if tmp:
                pathValue = tmp[0][0].rstrip('/')
            else:
                pathValue = pathVariable

            # TODO: investigate these options in more detail!
            if not isinstance(pathValue,str):
              return;

            capitalArguments = [x.upper() for x in arguments]

            if 'BASE_DIR' in capitalArguments:
                if not len(pathValue) or pathValue[0]!='/':
                    base_dir_idx = capitalArguments.index('BASE_DIR') + 1
                    baseAddr = vmodel.expand([arguments[base_dir_idx]]).getValue()
                    pathValue = os.path.join(baseAddr, pathValue).rstrip('/')
            if isinstance(pathValue,RefNode):
                pathValue = flattenAlgorithmWithConditions(pathValue)

            if 'DIRECTORY' in capitalArguments or 'PATH' in capitalArguments:
                pathValue = os.path.dirname(pathValue)

            if 'NAME' in capitalArguments:
                pathValue = os.path.basename(pathValue)

            if 'EXT' in capitalArguments:
                name = os.path.basename(pathValue)
                parts = name.split('.')
                if len(parts)>1:
                    pathValue = '.'+'.'.join(parts[1:])
                else:
                    pathValue = name


            if 'NAME_WE'  in capitalArguments:
                name = os.path.basename(pathValue)
                pathValue = name.split('.')[0]

            if 'LAST_EXT' in capitalArguments:
                name = os.path.basename(pathValue)
                parts = name.split('.')
                if len(parts) > 1:
                    pathValue = '.'+parts[-1]
                else:
                    pathValue = ''

            if 'LAST_EXT' in capitalArguments:
                name = os.path.basename(pathValue)
                parts = name.split('.')
                if len(parts) > 1:
                    pathValue = '.'+parts[-1]
                else:
                    pathValue = ''

            if 'NAME_WLE' in capitalArguments:
                name = os.path.basename(pathValue)
                parts = name.split('.')
                if len(parts) > 1:
                    pathValue = parts[:-1]
                else:
                    pathValue = parts[0]


            node = util_create_and_add_refNode_for_variable(varName,commandNode,relatedProperty=pathValue)
            commandNode.commands.append(LiteralNode(pathValue, pathValue))
            # setCommand([varName,pathValue])


        # build_command(<variable>
        #       [CONFIGURATION <config>]
        #       [TARGET <target>]
        #       [PROJECT_NAME <projname>] # legacy, causes warning
        #      )
        elif commandId == 'build_command':
            varName = arguments.pop(0)
            commandNode = CustomCommandNode("build_command_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            refNode = RefNode("{}_{}".format(varName, vmodel.getNextCounter()), commandNode)
            lookupTable.setKey("${{{}}}".format(varName), refNode)

            vmodel.nodes.append(refNode)

        # create_test_sourcelist(sourceListName driverName
        #                test1 test2 test3
        #                EXTRA_INCLUDE include.h
        #                FUNCTION function)
        elif commandId == 'create_test_sourcelist':
            commandNode = CustomCommandNode("create_test_sourcelist_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # get_property(<variable>
        #      <GLOBAL             |
        #       DIRECTORY [dir]    |
        #       TARGET    <target> |
        #       SOURCE    <source> |
        #       INSTALL   <file>   |
        #       TEST      <test>   |
        #       CACHE     <entry>  |
        #       VARIABLE>
        #      PROPERTY <name>
        #      [SET | DEFINED | BRIEF_DOCS | FULL_DOCS])
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # get_source_file_property(VAR file property)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # get_target_property(VAR target property)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # get_test_property(test property VAR)
        elif commandId in ('get_property', 'get_source_file_property',
                           'get_target_property', 'get_test_property'):
            varName = arguments.pop(0)
            commandNode = CustomCommandNode("{}_{}".format(commandId, vmodel.getNextCounter()))
            refNode = RefNode("{}_{}".format(varName, vmodel.getNextCounter()), commandNode)
            lookupTable.setKey("${{{}}}".format(varName), refNode)
            vmodel.nodes.append(refNode)
            otherArgs = vmodel.expand(arguments)
            commandNode.commands.append(otherArgs)

        # set_property(<GLOBAL                    |
        #       DIRECTORY [dir]                   |
        #       TARGET    [target1 [target2 ...]] |
        #       SOURCE    [src1 [src2 ...]]       |
        #       INSTALL   [file1 [file2 ...]]     |
        #       TEST      [test1 [test2 ...]]     |
        #       CACHE     [entry1 [entry2 ...]]>
        #      [APPEND] [APPEND_STRING]
        #      PROPERTY <name> [value1 [value2 ...]])
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # set_source_files_properties([file1 [file2 [...]]]
        #                     PROPERTIES prop1 value1
        #                     [prop2 value2 [...]])
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # set_target_properties(target1 target2 ...
        #               PROPERTIES prop1 value1
        #               prop2 value2 ...)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # set_tests_properties(test1 [test2...] PROPERTIES prop1 value1 prop2 value2)
        # TODO: we have different implementation for these commands and set_directory_properties
        elif commandId in ('set_property', 'set_source_files_properties',
                           'set_target_properties', 'set_tests_properties'):
            commandNode = CustomCommandNode("{}".format(commandId))
            commandNode.commands.append(vmodel.expand(arguments))
            finalNode = util_handleConditions(commandNode, commandNode.name, None)
            vmodel.nodes.append(finalNode)

        # define_property(<GLOBAL | DIRECTORY | TARGET | SOURCE |
        #          TEST | VARIABLE | CACHED_VARIABLE>
        #          PROPERTY <name> [INHERITED]
        #          BRIEF_DOCS <brief-doc> [docs...]
        #          FULL_DOCS <full-doc> [docs...])
        elif commandId == 'define_property':
            _inherited = False
            scope = arguments.pop(0)
            arguments.pop(0)  # This is always PROPERTY
            propertyName = arguments.pop(0)  # TODO: This could be a variable, we should expand this
            if arguments[0] == 'INHERITED':
                _inherited = True
                arguments.pop(0)
            brief_doc = arguments[arguments.index('BRIEF_DOCS') + 1]
            full_doc = arguments[arguments.index('FULL_DOCS') + 1]
            scopeMap = vmodel.definedProperties.get(scope)
            scopeMap[propertyName] = {'INHERITED': _inherited, 'BRIEF_DOCS': brief_doc, 'FULL_DOCS': full_doc}

        elif commandId == 'export':
            commandNode = CustomCommandNode("EXPORT")
            commandNode.commands.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # TODO: Current implementation of function does not support nested one. We should change this
        elif commandId == 'function':
            functionName = arguments.pop(0)
            vmodel.functions[functionName] = {'arguments': arguments, 'commands': [], 'isMacro': False}
            vmodel.currentFunctionCommand = vmodel.functions[functionName]['commands']

        elif commandId == 'endfunction':
            vmodel.currentFunctionCommand = None

        # TODO: Current implementation of macro does not support nested one. We should change this
        elif commandId == 'macro':
            macroName = arguments.pop(0)
            vmodel.functions[macroName] = {'arguments': arguments, 'commands': [], 'isMacro': True}
            vmodel.currentFunctionCommand = vmodel.functions[macroName]['commands']

        elif commandId == 'endmacro':
            vmodel.currentFunctionCommand = None

        # TODO: We didn't check for if condition. We should write a function that handles all functions like this
        elif commandId == 'configure_file':
            configureFile = CustomCommandNode('configure_file')
            nextNode = vmodel.expand(arguments)
            configureFile.pointTo.append(nextNode)
            vmodel.nodes.append(configureFile)

        # TODO: Same as previous command, on top of that, we define new variables here, so there are problems
        #       with conditions
        elif commandId == 'execute_process':
            executeProcess = CustomCommandNode('execute_process')
            if 'RESULT_VARIABLE' in arguments:
                resultVariable = arguments[arguments.index('RESULT_VARIABLE') + 1]
                refNode = RefNode('{}_{}'.format(resultVariable, vmodel.getNextCounter()), executeProcess)
                lookupTable.setKey('${{{}}}'.format(resultVariable), refNode)
                vmodel.nodes.append(refNode)

            if 'OUTPUT_VARIABLE' in arguments:
                outputVariable = arguments[arguments.index('OUTPUT_VARIABLE') + 1]
                refNode = RefNode('{}_{}'.format(outputVariable, vmodel.getNextCounter()), executeProcess)
                lookupTable.setKey('${{{}}}'.format(outputVariable), refNode)
                vmodel.nodes.append(refNode)

            if 'ERROR_VARIABLE' in arguments:
                errorVariable = arguments[arguments.index('ERROR_VARIABLE') + 1]
                refNode = RefNode('{}_{}'.format(errorVariable, vmodel.getNextCounter()), executeProcess)
                lookupTable.setKey('${{{}}}'.format(errorVariable), refNode)
                vmodel.nodes.append(refNode)

            executeProcess.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(executeProcess)

        # TODO: We should change variable definition to handle all creations and modifications of variables
        elif commandId == 'site_name':
            siteNameNode = CustomCommandNode('site_name_{}'.format(vmodel.getNextCounter()))
            variableName = arguments[0]
            refNode = RefNode("{}_{}".format(variableName, vmodel.getNextCounter()), siteNameNode)
            lookupTable.setKey("${{{}}}".format(variableName), refNode)
            siteNameNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(refNode)

        elif commandId == 'separate_arguments':
            commandNode = CustomCommandNode('separate_arguments_{}'.format(vmodel.getNextCounter()))
            varName = arguments.pop(0)
            commandNode.pointTo.append(vmodel.expand(arguments))
            refNode = RefNode("{}_{}".format(varName, vmodel.getNextCounter()), commandNode)
            lookupTable.setKey("${{{}}}".format(varName), refNode)
            vmodel.nodes.append(refNode)

        elif commandId == 'cmake_minimum_required':
            version = arguments[1]
            vmodel.cmakeVersion = version

        # try_run(RUN_RESULT_VAR COMPILE_RESULT_VAR
        #         bindir srcfile [CMAKE_FLAGS <Flags>]
        #         [COMPILE_DEFINITIONS <flags>]
        #         [COMPILE_OUTPUT_VARIABLE comp]
        #         [RUN_OUTPUT_VARIABLE run]
        #         [OUTPUT_VARIABLE var]
        #         [ARGS <arg1> <arg2>...])
        elif commandId == 'try_run':
            runResultVar = arguments.pop(0)
            compileResultVar = arguments.pop(0)
            compileOutputVar = util_extract_variable_name('COMPILE_OUTPUT_VARIABLE', arguments)
            runOutputVar = util_extract_variable_name('RUN_OUTPUT_VARIABLE', arguments)
            outputVar = util_extract_variable_name('OUTPUT_VARIABLE', arguments)

            commandNode = CustomCommandNode("try_run_{}".format(vmodel.getNextCounter()))
            commandNode.commands.append(vmodel.expand(arguments))
            # Essential variables
            util_create_and_add_refNode_for_variable(runResultVar, commandNode,
                                                     relatedProperty='RUN_RESULT_VAR')
            util_create_and_add_refNode_for_variable(compileResultVar, commandNode,
                                                     relatedProperty='COMPILE_RESULT_VAR')
            # Optional Variables
            if compileOutputVar:
                util_create_and_add_refNode_for_variable(compileOutputVar, commandNode,
                                                         relatedProperty='COMPILE_OUTPUT_VARIABLE')
            if runOutputVar:
                util_create_and_add_refNode_for_variable(runOutputVar, commandNode,
                                                         relatedProperty='RUN_OUTPUT_VARIABLE')
            if outputVar:
                util_create_and_add_refNode_for_variable(outputVar, commandNode,
                                                         relatedProperty='OUTPUT_VARIABLE')

        # try_compile(RESULT_VAR <bindir> <srcdir>
        #     <projectName> [targetName] [CMAKE_FLAGS flags...]
        #     [OUTPUT_VARIABLE <var>])
        elif commandId == 'try_compile':
            resultVar = arguments.pop(0)
            outputVar = util_extract_variable_name('OUTPUT_VARIABLE', arguments)
            commandNode = CustomCommandNode("try_compile_{}".format(vmodel.getNextCounter()))
            commandNode.commands.append(vmodel.expand(arguments))
            # Essential variable
            util_create_and_add_refNode_for_variable(resultVar, commandNode,
                                                     relatedProperty="RESULT_VAR")
            # Optional variable
            if outputVar:
                util_create_and_add_refNode_for_variable(outputVar, commandNode,
                                                         relatedProperty='OUTPUT_VARIABLE')
        # target_sources( < target >
        #                 < INTERFACE | PUBLIC | PRIVATE > [items1...]
        #                 [ < INTERFACE | PUBLIC | PRIVATE > [items2...]...])
        elif commandId == 'target_sources':
            targetName = arguments.pop(0)
            targetInstance = lookupTable.getKey("t:{}".format(targetName))
            assert isinstance(targetInstance, TargetNode)
            sources = []
            interfaceSources = []
            while arguments:
                if arguments[0] in ('INTERFACE', 'PUBLIC', 'PRIVATE'):
                    scope = arguments.pop(0)
                sourceItem = arguments.pop(0)
                if scope.upper() in ('PRIVATE', 'PUBLIC'):
                    sources.append(sourceItem)
                if scope.upper() in ('INTERFACE', 'PUBLIC'):
                    interfaceSources.append(sourceItem)

            if sources:
                expandedSources = vmodel.expand(sources, True)
                assert isinstance(expandedSources, ConcatNode)
                if targetInstance.sources:
                    expandedSources.listOfNodes = targetInstance.sources.listOfNodes + expandedSources.listOfNodes
                    targetInstance.sources = util_handleConditions(expandedSources,
                                                                   expandedSources.name,
                                                                   targetInstance.sources)
                else:
                    targetInstance.sources = util_handleConditions(expandedSources,
                                                                   expandedSources.name)

            if interfaceSources:
                expandedInterfaceSources = vmodel.expand(interfaceSources, True)
                assert isinstance(expandedInterfaceSources, ConcatNode)
                if targetInstance.interfaceSources:
                    expandedInterfaceSources.listOfNodes = targetInstance.interfaceSources.listOfNodes + \
                                                           expandedInterfaceSources.listOfNodes
                    targetInstance.interfaceSources = util_handleConditions(expandedInterfaceSources,
                                                                            expandedInterfaceSources.name,
                                                                            targetInstance.interfaceSources)
                else:
                    targetInstance.interfaceSources = util_handleConditions(expandedInterfaceSources,
                                                                            expandedInterfaceSources.name)

        # target_compile_features(<target> <PRIVATE|PUBLIC|INTERFACE> <feature> [...])
        # This code is very similar to target_sources but I couldn't merge them
        elif commandId == 'target_compile_features':
            targetName = arguments.pop(0)
            targetInstance = lookupTable.getKey("t:{}".format(targetName))
            assert isinstance(targetInstance, TargetNode)
            features = []
            interfaceFeatures = []
            while arguments:
                if arguments[0] in ('INTERFACE', 'PUBLIC', 'PRIVATE'):
                    scope = arguments.pop(0)
                featureItem = arguments.pop(0)
                if scope.upper() in ('PRIVATE', 'PUBLIC'):
                    features.append(featureItem)
                if scope.upper() in ('INTERFACE', 'PUBLIC'):
                    interfaceFeatures.append(featureItem)

            if features:
                expandedSources = vmodel.expand(features, True)
                assert isinstance(expandedSources, ConcatNode)
                if targetInstance.compileFeatures:
                    expandedSources.listOfNodes = targetInstance.compileFeatures.listOfNodes + \
                                                  expandedSources.listOfNodes
                    targetInstance.compileFeatures = util_handleConditions(expandedSources,
                                                                           expandedSources.name,
                                                                           targetInstance.compileFeatures)
                else:
                    targetInstance.compileFeatures = util_handleConditions(expandedSources,
                                                                           expandedSources.name)

            if interfaceFeatures:
                expandedInterfaceFeatures = vmodel.expand(interfaceFeatures, True)
                assert isinstance(expandedInterfaceFeatures, ConcatNode)
                if targetInstance.interfaceCompileFeatures:
                    expandedInterfaceFeatures.listOfNodes = targetInstance.interfaceCompileFeatures.listOfNodes + \
                                                            expandedInterfaceFeatures.listOfNodes
                    targetInstance.interfaceCompileFeatures = \
                        util_handleConditions(expandedInterfaceFeatures,
                                              expandedInterfaceFeatures.name,
                                              targetInstance.interfaceCompileFeatures)
                else:
                    targetInstance.interfaceCompileFeatures = util_handleConditions(expandedInterfaceFeatures,
                                                                                    expandedInterfaceFeatures.name)
        # target_compile_options(<target> [BEFORE]
        #           <INTERFACE|PUBLIC|PRIVATE> [items1...]
        #           [<INTERFACE|PUBLIC|PRIVATE> [items2...] ...])
        # The code is very similar to target_sources and previous command, but I couldn't merge them
        elif commandId == 'target_compile_options':
            targetName = arguments.pop(0)
            targetInstance = lookupTable.getKey("t:{}".format(targetName))
            assert isinstance(targetInstance, TargetNode)
            options = []
            interfaceOptions = []
            while arguments:
                if arguments[0] in ('INTERFACE', 'PUBLIC', 'PRIVATE'):
                    scope = arguments.pop(0)
                featureItem = arguments.pop(0)
                if scope.upper() in ('PRIVATE', 'PUBLIC'):
                    options.append(featureItem)
                if scope.upper() in ('INTERFACE', 'PUBLIC'):
                    interfaceOptions.append(featureItem)

            if options:
                expandedOptions = vmodel.expand(options, True)
                assert isinstance(expandedOptions, ConcatNode)
                if targetInstance.compileOptions:
                    expandedOptions.listOfNodes = targetInstance.compileOptions.listOfNodes + \
                                                  expandedOptions.listOfNodes
                    targetInstance.compileOptions = util_handleConditions(expandedOptions,
                                                                          expandedOptions.name,
                                                                          targetInstance.compileOptions)
                else:
                    targetInstance.compileOptions = util_handleConditions(expandedOptions,
                                                                          expandedOptions.name)

            if interfaceOptions:
                expandedInterfaceOptions = vmodel.expand(interfaceOptions, True)
                assert isinstance(expandedInterfaceOptions, ConcatNode)
                if targetInstance.interfaceCompileOptions:
                    expandedInterfaceOptions.listOfNodes = targetInstance.interfaceCompileOptions.listOfNodes + \
                                                           expandedInterfaceOptions.listOfNodes
                    targetInstance.interfaceCompileOptions = \
                        util_handleConditions(expandedInterfaceOptions,
                                              expandedInterfaceOptions.name,
                                              targetInstance.interfaceCompileOptions)
                else:
                    targetInstance.interfaceCompileOptions = util_handleConditions(expandedInterfaceOptions,
                                                                                   expandedInterfaceOptions.name)


        # TODO: If we are in a condition, instead of overwriting the value of the property,
        #       we should add a select node and keep the current value
        # set_directory_properties(PROPERTIES prop1 value1 prop2 value2)
        elif commandId == 'set_directory_properties':
            # We throw the first argument away as it is always PROPERTIES
            arguments.pop(0)
            while arguments:
                propertyName = arguments.pop(0)
                propertyConcatNode = ConcatNode("{}_{}".format(propertyName, vmodel.getNextCounter()))
                propertyConcatNode.addNode(vmodel.expand([arguments.pop(0)]))
                vmodel.DIRECTORY_PROPERTIES.setKey(propertyName, propertyConcatNode)

        # 1. get_directory_property(<variable> [DIRECTORY <dir>] <prop-name>)
        # 2. get_directory_property(<variable> [DIRECTORY <dir>] DEFINITION <var-name>)
        elif commandId == 'get_directory_property':
            varName = arguments.pop(0)
            propertyLookupTable = vmodel.DIRECTORY_PROPERTIES
            if 'DIRECTORY' in arguments:
                arguments.pop(0)
                dirName = arguments.pop(0)
                propertyLookupTable = vmodel.directory_to_properties.get(dirName)

            # This is for the second signature of the command
            if 'DEFINITION' in arguments:
                arguments.pop(0)
                varNameToLookup = arguments.pop(0)
                nextNode = propertyLookupTable.getKey('VARIABLES').get('${{{}}}'.format(varNameToLookup))
            else:
                propertyName = arguments.pop(0)
                propertyNode = propertyLookupTable.getKey(propertyName)
                nextNode = propertyNode
            refNode = RefNode('{}_{}'.format(varName, vmodel.getNextCounter()), nextNode)
            lookupTable.setKey('${{{}}}'.format(varName), refNode)
            vmodel.nodes.append(refNode)
        # 23 different variant of this command explained at https://cmake.org/cmake/help/v3.1/command/string.html
        elif commandId == 'string':
            stringCommandNode = CustomCommandNode("string_{}".format(vmodel.getNextCounter()))
            commandType = arguments[0]
            if commandType == 'REGEX':
                regexType = arguments[1]
                if regexType in ('MATCH', 'MATCHALL'):
                    outVar = arguments.pop(3)
                elif regexType == 'REPLACE':
                    outVar = arguments.pop(4)
            elif commandType in ('REPLACE', 'FIND'):
                outVar = arguments.pop(3)
            elif commandType in ('CONCAT', 'MD5', 'SHA1', 'SHA224', 'SHA256', 'SHA384', 'SHA512', 'TIMESTAMP', 'UUID'):
                outVar = arguments.pop(1)
            elif commandType in ('COMPARE', 'SUBSTRING'):
                outVar = arguments.pop(4)
            elif commandType in ('ASCII', 'RANDOM'):
                outVar = arguments.pop()
            elif commandType in ('APPEND', 'PREPEND'):
                outVar = arguments.pop()
            elif commandType in ('CONFIGURE', 'TOUPPER', 'TOLOWER', 'LENGTH', 'STRIP',
                                 'MAKE_C_IDENTIFIER', 'GENEX_STRIP'):
                outVar = arguments.pop(2)

            util_create_and_add_refNode_for_variable(outVar, stringCommandNode)
            stringCommandNode.commands.append(vmodel.expand(arguments))

        # get_cmake_property(VAR property)
        elif commandId == 'get_cmake_property':
            varName = arguments.pop(0)
            propertyName = arguments.pop(0)
            result = []
            for directory in vmodel.directory_to_properties:
                properties = vmodel.directory_to_properties.get(directory)
                if properties.getKey(propertyName):
                    propertyDic = properties.getKey(propertyName)
                    result += list(propertyDic.keys())
            concatNode = ConcatNode("get_cmake_property_{}_{}".format(propertyName, vmodel.getNextCounter()))
            for item in result:
                # TODO: A very very very bad code to extract variable name. So, we are converting
                #       ${foo} to foo
                if item[0] == '$':
                    item = item[2:-1]
                concatNode.addNode(LiteralNode(item, item))

            refNode = RefNode("{}_{}".format(varName, vmodel.getNextCounter()), concatNode)
            lookupTable.setKey("${{{}}}".format(varName), refNode)
            vmodel.nodes.append(refNode)

        elif commandId == 'while':
            whileCommand(arguments)

        elif commandId == 'endwhile':
            endwhileCommand()

        # break()
        elif commandId == 'break':
            breakCommand = CustomCommandNode("break")
            vmodel.nodes.append(util_handleConditions(breakCommand, breakCommand.getName()))

        # return()
        elif commandId == 'return':
            pass

        elif commandId == 'unset':
            variable_name = "${{{}}}".format(arguments.pop(0))
            parentScope = False
            if "PARENT_SCOPE" in arguments:
                parentScope = True
            lookupTable.deleteKey(variable_name, parentScope)

        elif commandId == 'foreach':
            forEachCommand(arguments)

        elif commandId == 'endforeach':
            lastPushedLookup = vmodel.getLastPushedLookupTable()
            rule = vmodel.popSystemState()
            assert rule.getType() == 'foreach'
            command = rule.command
            # forEachVariableName = command.commands[0].getChildren()[0].getValue()
            prevNodeStack = vmodel.nodeStack.pop()
            for item in vmodel.nodes:
                if item not in prevNodeStack:
                    command.depends.append(item)
            for key in lookupTable.items[-1].keys():
                if key not in lastPushedLookup.items[-1].keys() or \
                        lookupTable.getKey(key) != lastPushedLookup.getKey(key):
                    # We don't want to create a ref node for the variable that is the argument of foreach command
                    # if key == "${{{}}}".format(forEachVariableName):s
                    #     continue
                    refNode = RefNode("{}_{}".format(key, vmodel.getNextCounter()), command)
                    lookupTable.setKey(key, refNode)
                    vmodel.nodes.append(refNode)
            if command not in vmodel.nodes:
                vmodel.nodes.append(command)

        elif commandId == 'add_subdirectory':
            tempProjectDir = project_dir
            if os.path.exists(os.path.join(project_dir, ctx.argument().single_argument()[0].getText())):
                project_dir = os.path.join(project_dir, ctx.argument().single_argument()[0].getText())
            else:
                project_dir =  ctx.argument().single_argument()[0].getText()
            # TODO check if we need to bring anything from the new state
            lookupTable.newScope()

            logging.info('start new file {}'.format((str)(os.path.join(project_dir, 'CMakeLists.txt'))))
            possible_paths = flattenAlgorithmWithConditions(vmodel.expand([project_dir]))
            # First 0 for getting the only element in possible path,
            # Second 0 for getting the key (path)
            project_dir = possible_paths[0][0]
            util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR',
                                                     LiteralNode(project_dir, project_dir))
            parent_dir = directoryTree.find(tempProjectDir)
            child_dir = directoryTree.find(project_dir)
            if child_dir is None:
                child_dir = DirectoryNode(project_dir)
            directoryTree.addChild(parent_dir, child_dir)
            parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
            # parseFile(os.path.join(possible_paths[0][0], 'CMakeLists.txt'),True)
            lookupTable.dropScope()
            project_dir = tempProjectDir

        elif commandId == 'aux_source_directory':
            directory = arguments.pop(0)
            variable_name = arguments.pop()
            try: # TODO: Some CMake variables like CMAKE_BINARY_DIR are not implemented
                flatted_directory = flattenAlgorithmWithConditions(vmodel.expand([directory]))[0][0]
                files = glob.glob(os.path.join(flatted_directory, '*.c')) + \
                    glob.glob(os.path.join(flatted_directory, '*.h')) + \
                    glob.glob(os.path.join(flatted_directory, '*.cpp'))
                if not files:
                    files.append(flatted_directory)
            except IndexError:
                files = []
            node = util_create_and_add_refNode_for_variable(variable_name, vmodel.expand(files))
            vmodel.nodes.append(node)

        elif commandId == 'add_library':
            directory_node = directoryTree.find(project_dir)
            target_nodes = addTarget(arguments, False)
            for target_node in target_nodes:
                directory_node.targets.append(target_node)
    
        elif commandId == 'add_executable':
            directory_node = directoryTree.find(project_dir)
            target_nodes = addTarget(arguments, True)
            for target_node in target_nodes:
                directory_node.targets.append(target_node)

        elif commandId == 'list':
            listCommand(arguments)

        elif commandId == 'file':
            fileCommand(arguments, project_dir)

        # target_include_directories( < target > [SYSTEM][BEFORE]
        #         < INTERFACE | PUBLIC | PRIVATE > [items1...]
        #       [ < INTERFACE | PUBLIC | PRIVATE > [items2...]...])
        elif commandId == 'target_include_directories':
            targetName = arguments.pop(0)
            targetName = flattenAlgorithmWithConditions(vmodel.expand([targetName]))[0][0]
            targetNode = lookupTable.getKey("t:{}".format(targetName))
            assert isinstance(targetNode, TargetNode)
            includeDirectories = []
            interfaceIncludeDirectories = []
            interfaceSystemIncludeDirectories = []
            shouldPrepended = False
            systemArg = False

            if 'BEFORE' in arguments:
                shouldPrepended = True
                arguments.pop(arguments.index('BEFORE'))

            if 'SYSTEM' in arguments:
                systemArg = True
                arguments.pop(arguments.index('SYSTEM'))

            while arguments:
                if arguments[0] in ('INTERFACE', 'PUBLIC', 'PRIVATE'):
                    scope = arguments.pop(0)
                item = arguments.pop(0)
                if systemArg and scope.upper() in ('PUBLIC', 'INTERFACE'):
                    interfaceSystemIncludeDirectories.append(item)
                    continue
                if scope.upper() in ('PRIVATE', 'PUBLIC'):
                    includeDirectories.append(item)
                if scope.upper() in ('INTERFACE', 'PUBLIC'):
                    interfaceIncludeDirectories.append(item)

            def handleProperty(propertyList, targetProperty):
                if propertyList:
                    extendedProperties = vmodel.expand(propertyList, True)
                    assert isinstance(extendedProperties, ConcatNode)
                    if getattr(targetNode, targetProperty) is None:
                        setattr(targetNode, targetProperty, ConcatNode("{}_{}_{}"
                                                                       .format(targetNode.getName(),
                                                                               targetProperty,
                                                                               vmodel.getNextCounter())))
                    if shouldPrepended:
                        extendedProperties.listOfNodes = extendedProperties.listOfNodes + \
                                                         getattr(targetNode, targetProperty).listOfNodes
                    else:
                        extendedProperties.listOfNodes = getattr(targetNode, targetProperty).listOfNodes + \
                                                         extendedProperties.listOfNodes
                    setattr(targetNode, targetProperty,
                            util_handleConditions(extendedProperties,
                                                  extendedProperties.name,
                                                  getattr(targetNode, targetProperty)))

            handleProperty(includeDirectories, 'includeDirectories')
            handleProperty(interfaceIncludeDirectories, 'interfaceIncludeDirectories')
            handleProperty(interfaceSystemIncludeDirectories, 'interfaceSystemIncludeDirectories')

        elif commandId == 'add_compile_definitions':
            handleCompileDefinitionCommand(arguments, command='add', specific=True, project_dir=project_dir)

        elif commandId == 'add_compile_options':
            addCompileOptionsCommand(arguments)
        
        elif commandId == 'target_compile_definitions':
            addCompileTargetDefinitionsCommand(arguments)
        
        # link_libraries([item1 [item2 [...]]]
        #        [[debug|optimized|general] <item>] ...)
        elif commandId == 'link_libraries':
            addLinkLibraries(arguments)

        # link_directories(directory1 directory2 ...)
        elif commandId == 'link_directories':
            addLinkDirectories(arguments)

        elif commandId in ('target_link_libraries', 'add_dependencies'):
            customCommand = CustomCommandNode(commandId)
            customCommand.commands.append(vmodel.expand(arguments))
            # Next variable should have the target nodes itself or the name of targets
            targetList = flattenAlgorithmWithConditions(customCommand.commands[0].getChildren()[0])
            for target in targetList:
                targetNode = target[0]
                if not isinstance(targetNode, TargetNode):
                    targetNode = lookupTable.getKey("t:{}".format(targetNode))
                # Now we should have a TargetNode
                # assert isinstance(targetNode, TargetNode)
                # TODO: In some cases like find_package there could be an target in another package
                #  and we are not able to find it, for now, we just continue
                if not isinstance(targetNode, TargetNode):
                    continue
                assert isinstance(target[1], set)
                finalNode = util_handleConditions(customCommand, customCommand.name, None, target[1])
                targetNode.addLinkLibrary(finalNode)
                vmodel.nodes.append(finalNode)

        # project( < PROJECT - NAME > [ < language - name > ...])
        elif commandId == 'project':
            projectName = arguments.pop(0)
            vmodel.langs = list(arguments)
            capitalArguments = [x.upper() for x in arguments]
            projectVersion = None
            projectDescription = None
            if 'DESCRIPTION' in capitalArguments:
                descriptionIndex = arguments.index('DESCRIPTION')
                projectDescription = arguments[descriptionIndex+1]


            if 'VERSION' in capitalArguments:
                versionIndex = arguments.index('VERSION')
                projectVersion = vmodel.expand([arguments[versionIndex+1]])
                # # TODO: Add support for conditional versioning
                # projectVersion = flattenAlgorithmWithConditions(projectVersion)[0][0]

            util_create_and_add_refNode_for_variable(f'{projectName}_SOURCE_DIR', LiteralNode(project_dir, project_dir))
            if projectVersion:
                util_create_and_add_refNode_for_variable(f'{projectName}_VERSION', projectVersion)
            if projectDescription:
                util_create_and_add_refNode_for_variable(f'{projectName}_DESCRIPTION_DIR', LiteralNode(f'{projectName}_DESCRIPTION_DIR', projectDescription))

        elif commandId == 'cmake_dependent_option':
            optionName = arguments.pop(0)
            description = arguments.pop(0)
            initialValue = arguments.pop(0)
            depends = arguments.pop(0)

            depends = depends.replace('"', '')
            depends = depends.replace(';', ' ')
            depends = depends.split(' ')

            for idx, item in enumerate(depends):
                if lookupTable.getKey("${{{}}}".format(item)):
                    depends[idx] = "${{{}}}".format(item)

            optionNode = OptionNode(optionName)
            optionNode.description = description
            optionNode.default = True if initialValue.lower() == 'ON' else False
            optionNode.dependentOption = True
            optionNode.depends = vmodel.expand(depends)
            vmodel.addOption(optionName, True if initialValue.lower() == 'ON' else False)

            util_create_and_add_refNode_for_variable(optionName, optionNode)
        # install(TARGETS targets... [EXPORT <export-name>]
        #         [[ARCHIVE|LIBRARY|RUNTIME|OBJECTS|FRAMEWORK|BUNDLE|
        #           PRIVATE_HEADER|PUBLIC_HEADER|RESOURCE]
        #          [DESTINATION <dir>]
        #          [PERMISSIONS permissions...]
        #          [CONFIGURATIONS [Debug|Release|...]]
        #          [COMPONENT <component>]
        #          [NAMELINK_COMPONENT <component>]
        #          [OPTIONAL] [EXCLUDE_FROM_ALL]
        #          [NAMELINK_ONLY|NAMELINK_SKIP]
        #         ] [...]
        #         [INCLUDES DESTINATION [<dir> ...]]
        #         )
        elif commandId == 'install':
            commandNode = CustomCommandNode("install_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # include_directories([AFTER|BEFORE] [SYSTEM] dir1 [dir2 ...])
        elif commandId == 'include_directories':
            includeDirectories = []
            shouldPrepended = False
            systemArg = False

            if 'BEFORE' in arguments:
                shouldPrepended = True
                arguments.pop(arguments.index('BEFORE'))

            if 'AFTER' in arguments:
                arguments.pop(arguments.index('AFTER'))

            if 'SYSTEM' in arguments:
                systemArg = True
                arguments.pop(arguments.index('SYSTEM'))

            while arguments:
                item = arguments.pop(0)
                includeDirectories.append(item)

            def handleProperty(propertyList, targetProperty):
                if propertyList:
                    extendedProperties = vmodel.expand(propertyList, True)
                    # XXX Ask @mehran whether we need to keep this or not
                    # extendedPropertiesNodeWithConditions = util_handleConditions(extendedProperties, extendedProperties.name, None)
                    if len(propertyList)==1:
                        tmpConcatNode = ConcatNode("{}_{}".format(extendedProperties.name,vmodel.getNextCounter()))
                        tmpConcatNode.addNode(extendedProperties)
                        extendedProperties = tmpConcatNode

                    assert isinstance(extendedProperties, ConcatNode)
                    if not vmodel.DIRECTORY_PROPERTIES.getOwnKey('INCLUDE_DIRECTORIES'):
                        vmodel.DIRECTORY_PROPERTIES.setKey('INCLUDE_DIRECTORIES', extendedProperties)
                    else:
                        if shouldPrepended:
                            extendedProperties.listOfNodes = extendedProperties.listOfNodes + \
                                                                                vmodel.DIRECTORY_PROPERTIES.getKey('INCLUDE_DIRECTORIES').listOfNodes
                        else:
                            extendedProperties.listOfNodes = vmodel.DIRECTORY_PROPERTIES.getKey('INCLUDE_DIRECTORIES').listOfNodes + \
                                                                                extendedProperties.listOfNodes
                        vmodel.DIRECTORY_PROPERTIES.setKey('INCLUDE_DIRECTORIES', extendedProperties)

            handleProperty(includeDirectories, 'includeDirectories')

        # feature_summary( [FILENAME <file>]
        #          [APPEND]
        #          [VAR <variable_name>]
        #          [INCLUDE_QUIET_PACKAGES]
        #          [FATAL_ON_MISSING_REQUIRED_PACKAGES]
        #          [DESCRIPTION "<description>" | DEFAULT_DESCRIPTION]
        #          [QUIET_ON_EMPTY]
        #          WHAT (ALL
        #               | PACKAGES_FOUND | PACKAGES_NOT_FOUND
        #               | <TYPE>_PACKAGES_FOUND | <TYPE>_PACKAGES_NOT_FOUND
        #               | ENABLED_FEATURES | DISABLED_FEATURES)
        #        )
        elif commandId == 'feature_summary':
            commandNode = CustomCommandNode("feature_summary_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # set_package_properties(<name> PROPERTIES
        #                [ URL <url> ]
        #                [ DESCRIPTION <description> ]
        #                [ TYPE (RUNTIME|OPTIONAL|RECOMMENDED|REQUIRED) ]
        #                [ PURPOSE <purpose> ]
        #               )
        elif commandId == 'set_package_properties':
            commandNode = CustomCommandNode("set_package_properties_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # GENERATE_EXPORT_HEADER( LIBRARY_TARGET
        #           [BASE_NAME <base_name>]
        #           [EXPORT_MACRO_NAME <export_macro_name>]
        #           [EXPORT_FILE_NAME <export_file_name>]
        #           [DEPRECATED_MACRO_NAME <deprecated_macro_name>]
        #           [NO_EXPORT_MACRO_NAME <no_export_macro_name>]
        #           [INCLUDE_GUARD_NAME <include_guard_name>]
        #           [STATIC_DEFINE <static_define>]
        #           [NO_DEPRECATED_MACRO_NAME <no_deprecated_macro_name>]
        #           [DEFINE_NO_DEPRECATED]
        #           [PREFIX_NAME <prefix_name>]
        #           [CUSTOM_CONTENT_FROM_VARIABLE <variable>]
        # )
        # TODO: check with @Mehran if we really care about generating .h files since it is file level
        # headsup: it creates .h files
        elif commandId == 'generate_export_header':
            commandNode = CustomCommandNode("generate_export_header_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # configure_package_config_file(<input> <output>
        #     INSTALL_DESTINATION <path>
        #     [PATH_VARS <var1> <var2> ... <varN>]
        #     [NO_SET_AND_CHECK_MACRO]
        #     [NO_CHECK_REQUIRED_COMPONENTS_MACRO]
        #     [INSTALL_PREFIX <path>]
        #     )
        elif commandId == 'configure_package_config_file':
            commandNode = CustomCommandNode("configure_package_config_file_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)


        # https://cmake.org/cmake/help/latest/command/add_dependencies.html
        elif commandId == 'add_dependencies':
            target = arguments.pop(0)
            targetNode = vmodel.lookupTable.getKey("t:{}".format(target))
            assert isinstance(targetNode, TargetNode)
            for targetDependency in arguments:
                targetDependencyNode = vmodel.lookupTable.getKey("t:{}".format(targetDependency))
                assert isinstance(targetDependencyNode, TargetNode)
                # targetNode.depends.append(targetDependencyNode)
                targetNode.addLinkLibrary(targetDependencyNode)

        # https://cmake.org/cmake/help/latest/command/cmake_policy.html
        elif commandId == 'cmake_policy':
            commandNode = CustomCommandNode("cmake_policy_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://cmake.org/cmake/help/latest/command/enable_testing.html
        # XXX: Update add_test to be compatible with this command according to description here:
        # https://cmake.org/cmake/help/latest/command/add_test.html#command:add_test
        elif commandId == 'enable_testing':                   
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://cmake.org/cmake/help/v3.19/module/CheckTypeSize.html
        # TODO: add HAVE_${variable} in future
        elif commandId == 'check_type_size':                   
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)


        # ecm_qt_declare_logging_category(<sources_var_name(|target (since 5.80))>
        #     HEADER <filename>
        #     IDENTIFIER <identifier>
        #     CATEGORY_NAME <category_name>
        #     [OLD_CATEGORY_NAMES <oldest_cat_name> [<second_oldest_cat_name> [...]]]
        #     [DEFAULT_SEVERITY <Debug|Info|Warning|Critical|Fatal>]
        #     [EXPORT <exportid>]
        #     [DESCRIPTION <description>]
        # )
        # This command will add debugging and logging feature to QT
        # more info: https://api.kde.org/ecm/module/ECMQtDeclareLoggingCategory.html
        elif extension_type=='ECM' and commandId == 'ecm_qt_declare_logging_category':
            commandNode = CustomCommandNode("ecm_qt_declare_logging_category_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # ecm_add_test(<sources> LINK_LIBRARIES <library> [<library> [...]]
        #            [TEST_NAME <name>]
        #            [NAME_PREFIX <prefix>]
        #            [GUI])
        elif extension_type=='ECM' and commandId == 'ecm_add_test':
            ECMAddTest(arguments)

        # ecm_add_tests(<sources> LINK_LIBRARIES <library> [<library> [...]]
        #            [TEST_NAME <name>]
        #            [NAME_PREFIX <prefix>]
        #            [GUI])
        elif extension_type=='ECM' and commandId == 'ecm_add_tests':

            sources = []
            func_keys = ["link_libraries","NAME_PREFIX","GUI","TARGET_NAMES_VAR","TEST_NAMES_VAR"]
            while len(arguments) and arguments[0].lower() not in func_keys:
                sources.append(arguments.pop(0))

            target_name = '.'.join(sources[0].split('.')[:-1])
            libraries = []
            prefix = ""
            target_var_name = ""
            test_var_name = ""
            while len(arguments):
                key = arguments.pop(0).lower()
                values = []
                if key == "link_libraries":
                    while  len(arguments) and arguments[0].lower() not in func_keys:
                        values.append(arguments.pop(0))
                    libraries = values

                if key == "test_name":
                    arguments.pop(0)
                    target_name = arguments.pop(0)

                if key == "target_names_var":
                    target_var_name = arguments.pop(0)

                if key == "test_names_var":
                    test_var_name = arguments.pop(0)

                if key == "name_prefix":
                    arguments.pop(0)
                    prefix = arguments.pop(0)

            base_name = prefix + target_name
            if target_var_name:
                targert_names = [';'.join((prefix+'.'.join(source.split('.')[:-1]))) for source in sources]
                setCommand([target_var_name, targert_names])

            if test_var_name:
                test_names = [';'.join((prefix+'.'.join(source.split('.')[:-1]))) for source in sources]
                setCommand([test_var_name, test_names])



            for source in sources:
                if prefix:
                    ECMAddTest([source,"LINK_LIBRARIES"]+libraries+["NAME_PREFIX",prefix] )
                else:
                    ECMAddTest([source,"LINK_LIBRARIES"]+libraries )

        # ecm_mark_as_test(<target1> [<target2> [...]])
        elif extension_type=='ECM' and commandId == 'ecm_mark_as_test':
            for argument in arguments:
                # XXX
                # targetNode = vmodel.expand(target_link_arguments)
                targetNode = vmodel.lookupTable.getKey("t:{}".format(argument))
                targetConditions = flattenAlgorithmWithConditions(targetNode)
                assert isinstance(targetNode, TargetNode)
                # Here we are going to add condition

        # https://doc.qt.io/qt-5/qtwidgets-cmake-qt5-wrap-ui.html
        elif extension_type=='ECM' and commandId in ['ki18n_wrap_ui','qt5_wrap_ui']:
            # we just check if there is any error that stops the processing of cmake file
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # TODO: find a proper documentation
        elif extension_type=='ECM' and commandId == 'kde4_add_plugin':
            addTarget(arguments, False)


        # Code: https://github.com/KDE/kconfig/blob/master/KF5ConfigMacros.cmake
        # https://techbase.kde.org/ECM5/IncompatibleChangesKDELibs4ToECM
        # TODO: check with @Mehran if the config files are important
        elif extension_type=='ECM' and commandId in ['kconfig_add_kcfg_files','kde4_add_kcfg_files']:
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # ecm_generate_headers(<camelcase_forwarding_headers_var>
        #     HEADER_NAMES <CamelCaseName> [<CamelCaseName> [...]]
        #     [ORIGINAL <CAMELCASE|LOWERCASE>]
        #     [HEADER_EXTENSION <header_extension>]
        #     [OUTPUT_DIR <output_dir>]
        #     [PREFIX <prefix>]
        #     [REQUIRED_HEADERS <variable>]
        #     [COMMON_HEADER <HeaderName>]
        #     [RELATIVE <relative_path>])
        # https://github.com/KDAB/KDSoap/blob/master/cmake/ECMGenerateHeaders.cmake
        # TODO: Similar to 'generate_export_header'
        elif extension_type=='ECM' and commandId == 'ecm_generate_headers':
            commandNode = CustomCommandNode("ecm_generate_headers_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/kcoreaddons/blob/master/KF5CoreAddonsMacros.cmake
        # TODO: similar to 'generate_export_header'
        elif extension_type=='ECM' and commandId == 'kcoreaddons_desktop_to_json':
            commandNode = CustomCommandNode("kcoreaddons_desktop_to_json_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/extra-cmake-modules/blob/master/modules/ECMSetupVersion.cmake
        # TODO: similar to 'generate_export_header'
        # headsup: It also assign some variables so, we might want to set them
        elif extension_type=='ECM' and commandId == 'ecm_setup_version':
            commandNode = CustomCommandNode("ecm_setup_version_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/extra-cmake-modules/blob/master/modules/ECMInstallIcons.cmake
        # For kde4_install icons:https://github.com/KDE/kmag/commit/4507e6d698f0d6aef0102e80dabd984c06f81ea6
        # TODO: similar to 'generate_export_header'
        # headsup: It also assign some variables so, we might want to set them
        elif extension_type=='ECM' and commandId in ['ecm_install_icons','kde4_install_icons']:
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/extra-cmake-modules/blob/c0aa4d1692a6b7b8c00b8d9203379469cf3be531/modules/KDE4Macros.cmake#L752
        # https://invent.kde.org/graphics/krita/-/blob/2e9348b37e3b21cb7bfbd3f6839c28a005294467/cmake/kde_macro/KDE4Macros.cmake
        # XXX : Add condition for build, similar to 'ecm_mark_as_test'
        elif extension_type=='ECM' and commandId == 'kde4_add_unit_test':
            testName = arguments.pop(0)
            if arguments[0].upper() == "TESTNAME":
                arguments.pop(0)
                targetName = arguments.pop(0)
            else:
                targetName = testName
            # targetNode = vmodel.expand(testName)
            # executable = targetNode.pointTo.getValue()+'.bat' # XXX:ask @Mehran what happens if we have conditions on this? snf how to get all the conditional values
            testNode = TestNode(targetName)
            # testNode.command = vmodel.expand(executable)
            testNode.command = vmodel.expand(arguments)


            vmodel.nodes.append(testNode)

        # https://gitlab.kitware.com/cmake/community/-/wikis/doc/tutorials/How-To-Build-KDE4-Software
        elif extension_type=='ECM' and commandId == 'kde4_add_executable':
            addTarget(arguments, True)

        # https://doc.qt.io/qt-5.12/qtdbus-cmake-qt5-add-dbus-interface.html
        # TODO: similar to 'generate_export_header'
        # headsup: It also assign aadd outputted addresses to the first variable
        # https://doc.qt.io/qt-5/qtwidgets-cmake-qt5-wrap-ui.html
        # Been replace recently: https://techbase.kde.org/ECM5/IncompatibleChangesKDELibs4ToECM
        elif extension_type=='ECM' and commandId in ('qt5_add_dbus_interface','kde4_add_ui_files'):
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # qt5_add_dbus_adaptor(<VAR> dbus_spec header parent_class
        #          [basename]
        #          [classname])
        # Generates a C++ header file implementing an adaptor for a D-Bus interface description file defined
        # in dbus_spec. The path of the generated file is added to <VAR>. The generated adaptor class takes a
        #  pointer to parent_class as QObject parent. parent_class should be declared in header, which is
        # included in the generated code as #include "header".
        # TODO: similar to 'generate_export_header'
        # headsup: It also assign aadd outputted addresses to the first variable
        # https://cmake.org/cmake/help/latest/module/FindQt4.html
        elif extension_type=='ECM' and commandId in ['qt5_add_dbus_adaptor','qt4_add_dbus_adaptor']:
            commandNode = CustomCommandNode("{}ـ{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)


        # https://github.com/KDE/kdoctools/blob/master/KF5DocToolsMacros.cmake#L77
        elif extension_type=='ECM' and commandId == 'kdoctools_create_handbook':
            commandNode = CustomCommandNode("kdoctools_create_handbook_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/extra-cmake-modules/blob/fb0d05a8363b1f37c24f995b9565cb90c8625256/modules/MacroOptionalFindPackage.cmake
        elif extension_type=='ECM' and commandId == 'macro_optional_find_package':
            commandNode = CustomCommandNode("macro_optional_find_package_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://cmake.org/cmake/help/v3.19/module/FeatureSummary.html#command:add_feature_info
        elif extension_type=='ECM' and commandId == 'add_feature_info':
            commandNode = CustomCommandNode("add_feature_info_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://gitlab.kitware.com/cmake/community/-/wikis/doc/tutorials/How-To-Build-KDE4-Software
        elif extension_type=='ECM' and commandId == 'kde4_add_library':
            addTarget(arguments, False)

        # https://api.kde.org/ecm/module/ECMQtDeclareLoggingCategory.html
        elif extension_type=='ECM' and commandId == 'ecm_qt_install_logging_categories':
            commandNode = CustomCommandNode("ecm_qt_install_logging_categories_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/extra-cmake-modules/blob/26a5b6d0b901f5c6e1c8ef487a95678830ff5dbc/modules/MacroLogFeature.cmake#L29
        elif extension_type=='ECM' and commandId == 'macro_log_feature':
            commandNode = CustomCommandNode("macro_log_feature_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/kcoreaddons/blob/master/KF5CoreAddonsMacros.cmake
        # TODO: add installation process to the graph
        elif extension_type=='ECM' and commandId == 'kcoreaddons_add_plugin':
            plugin_name = arguments.pop(0)
            sources = []
            jsonName = ""
            installNamespace=""
            fields = ["SOURCES","JSON","INSTALL_NAMESPACE"]
            while arguments[0].upper() in fields:
                if arguments[0].upper() == "SOURCES":
                    arguments.pop(0)
                    while arguments[0].upper() not in fields:
                        sources.append(arguments.pop(0))
                elif arguments[0].upper() == "JSON":
                    arguments.pop(0)
                    jsonName = arguments.pop(0)
                elif arguments[0].upper() == "INSTALL_NAMESPACE":
                    arguments.pop(0)
                    installNamespace=arguments.pop(0)

            addTarget([plugin_name,"MODULE"]+sources)

        # https://api.kde.org/ecm/module/ECMGeneratePriFile.html
        # https://github.com/KDAB/KDStateMachineEditor/blob/master/cmake/ECMGeneratePriFile.cmake
        elif extension_type=='ECM' and commandId == 'ecm_generate_pri_file':
            commandNode = CustomCommandNode("ecm_generate_pri_file_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/IGNF/ContinuousGeneralisation/blob/master/ContinuousGeneralizer/Citations/eigen/bench/btl/cmake/MacroOptionalAddSubdirectory.cmake
        # https://github.com/KDE/extra-cmake-modules/blob/ea843d0852d7319a5a1ab3bf7a8c3cd9f823bdd6/modules/ECMOptionalAddSubdirectory.cmake
        elif extension_type=='ECM' and commandId in ['macro_optional_add_subdirectory', 'ecm_optional_add_subdirectory']:
            tempProjectDir = project_dir
            project_dir = os.path.join(project_dir, ctx.argument().single_argument()[0].getText())
            if(os.path.exists(project_dir)):
                # TODO check if we need to bring anything from the new state
                lookupTable.newScope()
                logging.info('start new file {} '.format(os.path.join(project_dir,'CMakeLists.txt')))
                parseFile(os.path.join(project_dir, 'CMakeLists.txt'),True)
                logging.info('finished new file {}'.format(os.path.join(project_dir, 'CMakeLists.txt')))
                lookupTable.dropScope()
            project_dir = tempProjectDir

        # https://github.com/KDE/knipptasch/blob/8d11ec10fe4f47e9c781b5e0d9f13dc3e6a13ddb/cmake/modules/MacroBoolTo01.cmake
        # XXX : really simple but need to talk with @Mehran about implementation of conditions
        elif extension_type=='ECM' and commandId == 'macro_bool_to_01':
            commandNode = CustomCommandNode("macro_bool_to_01_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)


        # https://api.kde.org/frameworks/ki18n/html/
        # https://github.com/KDE/ki18n/blob/9ddb73321624f87f3fa8da5fa441f9717dc06da5/cmake/KF5I18nMacros.cmake.in#L74
        elif extension_type=='ECM' and commandId == 'ki18n_install':
            commandNode = CustomCommandNode("ki18n_install_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)


        # https://api.kde.org/ecm/kde-module/KDECompilerSettings.html
        # https://github.com/KDE/extra-cmake-modules/blob/master/kde-modules/KDECompilerSettings.cmake#L318
        elif extension_type=='ECM' and commandId == 'kde_enable_exceptions':
            commandNode = CustomCommandNode("kde_enable_exceptions_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://api.kde.org/ecm/module/ECMMarkNonGuiExecutable.html
        # https://github.com/KDE/extra-cmake-modules/blob/ea843d0852d7319a5a1ab3bf7a8c3cd9f823bdd6/modules/ECMMarkNonGuiExecutable.cmake
        elif extension_type=='ECM' and commandId == 'ecm_mark_nongui_executable':
            for argument in arguments:
                commandNode = CustomCommandNode("set_target_properties_{}".format(vmodel.getNextCounter()))
                commandNode.pointTo.append(vmodel.expand([argument,'PROPERTIES','WIN32_EXECUTABLE','FALSE','MACOSX_BUNDLE','FALSE']))
                vmodel.nodes.append(commandNode)


        # https://github.com/KDE/calligra/blob/895c398bc22ecbab622487ddca69c66d26802ea7/cmake/modules/CalligraProductSetMacros.cmake#L215
        elif extension_type=='ECM' and commandId == 'calligra_define_product':
            commandNode = CustomCommandNode("calligra_define_product_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/smokegen/blob/f7126dca066d2b0a5f71a4ad48931181061a78b5/cmake/MacroOptionalAddBindings.cmake#L12
        # XXX: has to be handled dynamically later
        elif extension_type=='ECM' and commandId == 'macro_optional_add_bindings':
            commandNode = CustomCommandNode("macro_optional_add_bindings_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/kdoctools/blob/master/KF5DocToolsMacros.cmake#L211
        elif extension_type=='ECM' and commandId == 'kdoctools_install':
            commandNode = CustomCommandNode("macro_optional_add_bindings_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://api.kde.org/ecm/kde-module/KDEClangFormat.html
        elif extension_type=='ECM' and commandId == 'kde_clang_format':
            commandNode = CustomCommandNode("kde_clang_format_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)


        # https://cmake.org/cmake/help/latest/module/CheckCXXSourceCompiles.html
        # TODO: check functionality
        elif extension_type=='ECM' and commandId == 'check_cxx_source_compiles':
            selectNodeName = "SELECT_{}_{}".format('check_cxx_source_compiles',
                                               util_getStringFromList(arguments))
            newSelectNode = SelectNode(selectNodeName, arguments)
            newSelectNode.args = vmodel.expand(arguments)
            rule =  Rule()
            rule.setCondition(LocalVariable(arguments[1]))
            newSelectNode.rule = rule
            vmodel.nodes.append(newSelectNode)

        elif extension_type=='ECM' and commandId == 'kdoctools_create_manpage':
            commandNode = CustomCommandNode("kdoctools_create_manpage_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://api.kde.org/ecm/module/ECMAddQch.html
        elif extension_type=='ECM' and commandId == 'ecm_install_qch_export':
            targetNodeName = arguments[1]
            targetInstance = lookupTable.getKey("t:{}".format(targetNodeName))
            assert isinstance(targetInstance, TargetNode)
            commandNode = CustomCommandNode("install_{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://api.kde.org/ecm/module/ECMAddQch.html
        elif extension_type=='ECM' and commandId == 'ecm_add_qch_':
            commandNode = CustomCommandNode("kdoctools_create_manpage_{}".format(vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/extra-cmake-modules/blob/master/kde-modules/KDEGitCommitHooks.cmake
        elif extension_type=='ECM' and commandId == 'kde_configure_git_pre_commit_hook':
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/kde1-kdelibs/blob/master/cmake/Qt1Macros.cmake#L62
        elif extension_type=='ECM' and commandId == 'qt1_wrap_moc':
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)

        # https://github.com/KDE/kpackage/blob/master/KF5PackageMacros.cmake
        # TODO: check for add_custom_target in file
        elif extension_type=='ECM' and commandId == 'kpackage_install_package':
            commandNode = CustomCommandNode("{}_{}".format(commandId,vmodel.getNextCounter()))
            commandNode.pointTo.append(vmodel.expand(arguments))
            vmodel.nodes.append(commandNode)


        elif commandId=='cmake_parse_arguments':
            prefix = arguments.pop(0)
            options = arguments.pop(0).strip('"').split(';')
            oneValueKeywords = arguments.pop(0).strip('"').split(';')
            multiValueKeywords = arguments.pop(0).strip('"').split(';')
            args = flattenAlgorithmWithConditions(vmodel.expand(arguments))
            for idx,arg in enumerate(args):
                # TODO: add conditions!
                if arg[0] in oneValueKeywords:
                    if idx+1 < len(args):
                        setCommand([arg[0], args[idx+1][0]])
                elif arg[0] in options:
                    if idx + 1 < len(args):
                        setCommand([arg[0], args[idx+1][0]])
                elif arg[0] in multiValueKeywords:
                    valIdx = idx+1;
                    val=[];
                    while valIdx < len(args) and (args[valIdx][0] not in multiValueKeywords) and (args[valIdx][0] not in oneValueKeywords) \
                            and (args[valIdx][0] not in options):
                        val.append(args[valIdx][0])
                        valIdx += 1
                    setCommand([arg[0]]+val)

        elif commandId in no_op_commands:
            customCommand = CustomCommandNode("{}".format(commandId))
            customCommand.commands.append(vmodel.expand(arguments))
            vmodel.nodes.append(util_handleConditions(customCommand, customCommand.getName()))
        else:
            customFunction = vmodel.functions.get(commandId)
            if customFunction is None:
                print("[enterCommand_invocation] Command ignored: {}".format(commandId))
                return

            # Handle Max recursion for recursive functions
            global prevFunction
            global currentFunction
            global currentRecursionDepth
            global maxRecursionDepth

            currentFunction = commandId

            if len(prevFunction)!=0 and currentFunction in prevFunction:
                currentRecursionDepth += 1
            if maxRecursionDepth <= currentRecursionDepth:
                print(f"{commandId}:Max recursion reached! Exiting future calls...")
                return
            prevFunction.append(currentFunction)
            # Finish part one of max recursion

            if not customFunction.get('isMacro'):
                vmodel.lookupTable.newScope()
            functionArguments = customFunction.get('arguments')

            # Set the value of argc
            vmodel.lookupTable.setKey('${ARGC}', vmodel.expand([str(len(arguments))]))
            # Set the values for ARGV0 ARGV1 ...
            for idx, value in enumerate(arguments):
                vmodel.lookupTable.setKey('${ARGV' + str(idx) + '}', vmodel.expand([value]))
            # Set the values for ARGV, ARGN
            vmodel.lookupTable.setKey('${ARGV}', vmodel.expand(arguments))
            vmodel.lookupTable.setKey('${ARGN}', vmodel.expand(arguments[len(functionArguments):]))
            functionBody:str = customFunction.get('commands')

            for arg in functionArguments:
                # strip is a hacky fix for consecutive double quotes when input is pass multiple times as function inputs
                functionBody = functionBody.replace("${{{}}}".format(arg), arguments[functionArguments.index(arg)].strip('"'))

            lexer = CMakeLexer(InputStream(functionBody))
            stream = CommonTokenStream(lexer)
            parser = CMakeParser(stream)
            tree = parser.cmakefile()
            extractor = self
            walker = ParseTreeWalker()
            walker.walk(extractor, tree)

            # Restore state after running the function for max recursion
            if len(prevFunction) and currentFunction in prevFunction[0:-1]:
                currentRecursionDepth -= 1
            prevFunction.pop();
            # Finished restoring

            if not customFunction.get('isMacro'):
                vmodel.lookupTable.dropScope()


def getIncludePaths():
    global includes_paths
    basepath="/usr/share/"
    for fname in os.listdir(basepath):
        if fname.find('cmake') != -1:
            path = os.path.join(basepath, fname, 'Modules')
            if os.path.isdir(path):
                includes_paths.append(path)

def initialize(input,isPath):
    if isPath:
        project_dir = input
    else:
        project_dir = ''

    getIncludePaths()
    # Initializing the important variables
    util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR', LiteralNode(project_dir, project_dir))
    util_create_and_add_refNode_for_variable('CMAKE_SOURCE_DIR', LiteralNode(project_dir, project_dir))
    util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_DIR', LiteralNode(project_dir, project_dir))
    util_create_and_add_refNode_for_variable('CMAKE_VERSION', LiteralNode('cmakeVersion', '3.16'))
    util_create_and_add_refNode_for_variable('CMAKE_MODULE_PATH', ConcatNode('cmakeVersion'))
    # TODO: get these from the environment variables
    util_create_and_add_refNode_for_variable('CMAKE_PROJECT_VERSION_MAJOR', LiteralNode('VERSION_MAJOR', 3))
    util_create_and_add_refNode_for_variable('CMAKE_PROJECT_VERSION_MINOR', LiteralNode('VERSION_MINOR', 20))
    util_create_and_add_refNode_for_variable('CMAKE_PROJECT_VERSION_PATCH', LiteralNode('VERSOIN_PATCH', 0))
    util_create_and_add_refNode_for_variable('CMAKE_PROJECT_VERSION_TWAEK', LiteralNode('VERSION_TWEAK', 0))

    util_create_and_add_refNode_for_variable('HUPNP_VERSION_MAJOR', LiteralNode('HUPNP_VERSION_MAJOR', 1))
    util_create_and_add_refNode_for_variable('HUPNP_VERSION_MINOR', LiteralNode('VERSION_TWEAK', 1))
    util_create_and_add_refNode_for_variable('HUPNP_VERSION_PATCH', LiteralNode('VERSION_TWEAK', 1))

    if isPath:
        parseFile(os.path.join(project_dir, 'CMakeLists.txt'),True)
    else:
        parseFile(input,False)



def parseFile(fileInput,isPath=True):
    if isPath:
        inputFile = FileStream(fileInput, encoding='utf-8')
        util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_FILE',LiteralNode(fileInput, fileInput))
        util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR',
                                                 LiteralNode(f"parse_{fileInput}", fileInput))
    else:
        inputFile = InputStream(fileInput)
        util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_FILE',LiteralNode('no_file', ''))

    lexer = CMakeLexer(inputFile)
    stream = CommonTokenStream(lexer)
    parser = CMakeParser(stream)
    tree = parser.cmakefile()
    extractor = CMakeExtractorListener()
    walker = ParseTreeWalker()
    walker.walk(extractor, tree)


def getGraph(directory):
    global project_dir
    project_dir = directory
    # util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR', LiteralNode(project_dir, project_dir))
    # util_create_and_add_refNode_for_variable('CMAKE_SOURCE_DIR', LiteralNode(project_dir, project_dir))
    # util_create_and_add_refNode_for_variable('CMAKE_CURRENT_LIST_DIR', LiteralNode(project_dir, project_dir))
    # parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
    initialize(project_dir,True)
    vmodel.findAndSetTargets()
    linkDirectory()
    return vmodel, lookupTable


def linkDirectory():
    topological_order = directoryTree.getTopologicalOrder()
    # Setting the correct definition dependency based on directory
    for dir_node in topological_order:
        cur_dir = dir_node.rawName
        cur_dir_props = vmodel.directory_to_properties.get(cur_dir)

        # If there are directories that it depends on and they have directory-based definitions, 
        # it has to create an auxillary node that inherits parents' directory-based definitions.
        # Or if it is a root, then by definition, it is dependent on nothing.
        if not (dir_node == directoryTree.root or dir_node.depends_on):
            continue
        
        has_inheritance = False # to keep track of whether to remove the local_definitions_node later
        if cur_dir_props and (local_definition_node := cur_dir_props.getOwnKey('COMPILE_DEFINITIONS')):
            has_inheritance = True
        else:
            local_definition_node = DefinitionNode(from_dir=True, ordering=math.inf)
            if not cur_dir_props:
                vmodel.directory_to_properties[cur_dir] = Lookup()
            vmodel.directory_to_properties.get(cur_dir).setKey('COMPILE_DEFINITIONS', local_definition_node)

        for parent_node in dir_node.depends_on:
            parent_dir = parent_node.rawName
            parent_dir_props = vmodel.directory_to_properties.get(parent_dir)
            if not parent_dir_props or not (parent_definition_node := parent_dir_props.getOwnKey('COMPILE_DEFINITIONS')):
                # parent_definition_node = parent_dir_props.getOwnKey('COMPILE_DEFINITIONS')
                continue
            local_definition_node.addInheritance(parent_definition_node)
            has_inheritance = True

        if not has_inheritance:
            local_definition_node = None    
            del vmodel.directory_to_properties[cur_dir]

        # Merging target definitions and directory definitions for each single target, over all directories
        for target in dir_node.targets:
            concat_target_node = ConcatNode('merge_target_definition_{}'.format(vmodel.getNextCounter()))
            concat_interface_node = ConcatNode('merge_target_interface_definition_{}'.format(vmodel.getNextCounter()))
            if local_definition_node:
                concat_target_node.addNode(local_definition_node)
                # Depends on the exact definition, not really sure if directory definition
                # is part of interface definition
                # concat_interface_node.addNode(local_definition_node) 
            if target.definitions and isinstance(target.definitions, DefinitionNode):
                concat_target_node.addNode(target.definitions)
            if target.interfaceDefinitions and isinstance(target.interfaceDefinitions, DefinitionNode):
                concat_interface_node.addNode(target.interfaceDefinitions)
            if concat_target_node.getChildren():
                target.setDefinition(concat_target_node)
            if concat_interface_node.getChildren():
                target.setInterfaceDefinition(concat_interface_node)
                            

def getFlattenedDefintionsForTarget(target: str):
    return printDefinitionsForATarget(vmodel, lookupTable, target)


def getFlattenedFilesForTarget(target: str):
    return printFilesForATarget(vmodel, lookupTable, target)


def getTargets():
    vmodel.findAndSetTargets()
    for idx, item in enumerate(vmodel.targets):
        print(f'{idx}. {item.getValue()}')


def exportFlattenedListToCSV(flattened: Dict, fileName: str):
    CSV_HEADERS = ['file', 'condition']
    with open(fileName, 'w') as csv_out:
        writer = csv.DictWriter(csv_out, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for key in flattened.keys():
            writer.writerow({
                'file': flattened[key],
                'condition': key
            })


def main(argv):
    global extension_type
    extension_type = "ECM"
    if len(argv) > 2:
        currentIndex = 2;
        if argv[currentIndex]=='find_package_dir':
            dirs = argv[currentIndex+1].split(',')
            find_package_lookup_directories.append(dirs)
            currentIndex += 2

        if argv[currentIndex] == 'version':
            cmake_version = argv[currentIndex+1]
            for idx in range(len(find_package_lookup_directories)):
                find_package_lookup_directories[idx] = find_package_lookup_directories[idx].replace(':version',cmake_version)



    getGraph(argv[1])
    vmodel.export()
    # vmodel.checkIntegrity()
    # vmodel.findAndSetTargets()
    # doGitAnalysis(project_dir)
    # code.interact(local=dict(globals(), **locals()))
    # printInputVariablesAndOptions(vmodel, lookupTable)
    # printSourceFiles(vmodel, lookupTable)
    # testNode = vmodel.findNode('${CLIENT_LIBRARIES}_662')
    # flattenAlgorithmWithConditions(testNode)
    # a = printFilesForATarget(vmodel, lookupTable, argv[2], True)


if __name__ == "__main__":
    main(sys.argv)
