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

class CMakeExtractorListener(CMakeListener):
    rule: Optional[Rule] = None
    logicalExpressionStack: List[LogicalExpression] = []

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
        variableLookedUp = lookupTable.getKey(f'${{{ctx.getText()}}}')
        localVariable = LocalVariable(ctx.getText())
        if variableLookedUp:
            try:
                # Wherever we create a LocalVariable, we should flat the corresponding variable
                self.flattenVariableInConditionExpression(localVariable, variableLookedUp)
            except Z3Exception as e:
                print(localVariable)
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

        leftVariableLookedUp = lookupTable.getKey(f'${{{ctx_left_get_text}}}')
        rightVariableLookedUp = lookupTable.getKey(f'${{{ctx_right_get_text}}}')
        operator = ctx.operator.getText().upper()

        localVariableType = 'string' if operator in ('STRLESS', 'STREQUAL', 'STRGREATER', 'MATCHES') else 'int'
        constantExpressionType = ConstantExpression.Z3_STR if operator in ('STRLESS', 'STREQUAL',
                                                                           'STRGREATER', 'MATCHES') \
            else ConstantExpression.PYTHON_STR

        if leftVariableLookedUp:
            leftExpression = LocalVariable(ctx_left_get_text, localVariableType)
            self.flattenVariableInConditionExpression(leftExpression, leftVariableLookedUp)
        else:
            if ctx_left_get_text.upper().startswith('CMAKE_'):
                # Reserved variable for CMake
                variable_name = "${{{}}}".format(ctx_left_get_text)
                variableNode = RefNode("{}".format(variable_name), None)
                lookupTable.setKey(variable_name, variableNode)
                leftExpression = LocalVariable(ctx_left_get_text, localVariableType)
            else:
                leftExpression = ConstantExpression(ctx_left_get_text, constantExpressionType)

        if rightVariableLookedUp:
            rightExpression = LocalVariable(ctx_right_get_text, localVariableType)
            self.flattenVariableInConditionExpression(rightExpression, rightVariableLookedUp)
        else:
            if ctx_right_get_text.upper().startswith('CMAKE_'):
                # Reserved variable for CMake
                variable_name = "${{{}}}".format(ctx_right_get_text)
                variableNode = RefNode("{}".format(variable_name), None)
                lookupTable.setKey(variable_name, variableNode)
                rightExpression = LocalVariable(ctx_right_get_text, localVariableType)
            else:
                rightExpression = ConstantExpression(ctx_right_get_text, constantExpressionType)

        self.logicalExpressionStack.append(
            ComparisonExpression(leftExpression, rightExpression, operator)
        )

    def flattenVariableInConditionExpression(self, expression: LocalVariable, variable: Node):
        # Flattening the variable used inside the condition, like [(True, {bar}), (False, {Not bar, john > 2})]
        flattened = flattenAlgorithmWithConditions(variable) or []
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
                            rightHandSide = int(item[0].replace('.','', 1).replace('"', ''))
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

    def enterCommand_invocation(self, ctx: CMakeParser.Command_invocationContext):
        global project_dir
        commandId = ctx.Identifier().getText().lower()
        arguments = [child.getText() for child in ctx.argument().getChildren() if not isinstance(child, TerminalNode)]

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
            packageName = arguments[0]
            findPackageNode = CustomCommandNode("find_package_{}".format(vmodel.getNextCounter()))
            findPackageNode.commands.append(vmodel.expand(arguments))
            util_create_and_add_refNode_for_variable(packageName + "_FOUND", findPackageNode)

        # include( < file | module > [OPTIONAL][RESULT_VARIABLE < VAR >]
        #          [NO_POLICY_SCOPE])
        elif commandId == 'include':
            commandNode = CustomCommandNode("include")
            if 'RESULT_VARIABLE' in arguments:
                varIndex = arguments.index('RESULT_VARIABLE')
                arguments.pop(varIndex)  # This is RESULT_VAR
                util_create_and_add_refNode_for_variable(arguments.pop(varIndex), commandNode,
                                                         relatedProperty='RESULT_VARIABLE')


            args = vmodel.expand(arguments)
            commandNode.depends.append(args)

            # prevNodeStack = list(vmodel.nodes)
            # We execute the command if we can find the CMake file and there is no condition to execute it
            if os.path.exists(os.path.join(project_dir, args.getValue())):
                parseFile(os.path.join(project_dir, args.getValue()))
                # for item in vmodel.nodes:
                #     if item not in prevNodeStack:
                #         commandNode.commands.append(item)
            else:
                print("Cannot Find : {} to include".format(arguments))
                vmodel.nodes.append(util_handleConditions(commandNode, commandNode.getName()))

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
        elif commandId == 'get_filename_component':
            varName = arguments.pop(0)
            commandNode = CustomCommandNode("get_filename_component_{}".format(vmodel.getNextCounter()))
            refNode = RefNode("{}_{}".format(varName, vmodel.getNextCounter()), commandNode)
            lookupTable.setKey("${{{}}}".format(varName), refNode)
            vmodel.nodes.append(refNode)
            otherArgs = vmodel.expand(arguments)
            commandNode.commands.append(otherArgs)

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
                    # if key == "${{{}}}".format(forEachVariableName):
                    #     continue
                    refNode = RefNode("{}_{}".format(key, vmodel.getNextCounter()), command)
                    lookupTable.setKey(key, refNode)
                    vmodel.nodes.append(refNode)
            if command not in vmodel.nodes:
                vmodel.nodes.append(command)

        elif commandId == 'add_subdirectory':
            tempProjectDir = project_dir
            project_dir = os.path.join(project_dir, ctx.argument().single_argument()[0].getText())
            # TODO check if we need to bring anything from the new state
            lookupTable.newScope()

            print('start new file',os.path.join(project_dir, 'CMakeLists.txt'))
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
            target_node = addTarget(arguments, False)
            directory_node.targets.append(target_node)
            
        elif commandId == 'add_executable':
            directory_node = directoryTree.find(project_dir)
            target_node = addTarget(arguments, True)
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

        else:
            customFunction = vmodel.functions.get(commandId)
            if customFunction is None:
                customCommand = CustomCommandNode("{}".format(commandId))
                customCommand.commands.append(vmodel.expand(arguments))
                vmodel.nodes.append(util_handleConditions(customCommand, customCommand.getName()))
                return
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
                functionBody = functionBody.replace("${{{}}}".format(arg), arguments[functionArguments.index(arg)])

            lexer = CMakeLexer(InputStream(functionBody))
            stream = CommonTokenStream(lexer)
            parser = CMakeParser(stream)
            tree = parser.cmakefile()
            extractor = self
            walker = ParseTreeWalker()
            walker.walk(extractor, tree)
            if not customFunction.get('isMacro'):
                vmodel.lookupTable.dropScope()


def parseFile(filePath):
    inputFile = FileStream(filePath, encoding='utf-8')
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
    util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR', LiteralNode(project_dir, project_dir))
    util_create_and_add_refNode_for_variable('CMAKE_SOURCE_DIR', LiteralNode(project_dir, project_dir))
    parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
    vmodel.findAndSetTargets()
    linkDirectory()
    return vmodel, lookupTable


def linkDirectory():
    topological_order = directoryTree.getTopologicalOrder()
    # Setting the correct definition dependency based on directory
    for dir_node in topological_order:
        cur_dir = dir_node.rawName
        local_definition_node = vmodel.directory_to_properties.get(cur_dir).getOwnKey('COMPILE_DEFINITIONS')
        for parent_node in dir_node.depends_on:
            parent_dir = parent_node.rawName
            parent_definition_node = vmodel.directory_to_properties.get(parent_dir).getOwnKey('COMPILE_DEFINITIONS')
            local_definition_node.addInheritance(parent_definition_node)
    
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
    a = printFilesForATarget(vmodel, lookupTable, argv[2], True)


if __name__ == "__main__":
    main(sys.argv)
