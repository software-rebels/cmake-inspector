# Bultin Libraries
import sys
import os
from typing import List, Optional
# Third-party
from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
from antlr4.tree.Tree import TerminalNode
from neomodel import config
# Grammar generates by Antlr
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from grammar.CMakeListener import CMakeListener
# Our own library
from datastructs import RefNode, TargetNode, VModel, Lookup, SelectNode, ConcatNode, \
    CustomCommandNode, TestNode
from analyze import doGitAnalysis

config.DATABASE_URL = 'bolt://neo4j:123@localhost:7687'

project_dir = ""

vmodel = VModel.getInstance()
lookupTable = Lookup.getInstance()


def util_getStringFromList(lst: List):
    return " ".join(lst)


def setCommand(arguments):
    variable_name = "${{{}}}".format(arguments.pop(0))
    parentScope = False
    if 'PARENT_SCOPE' in arguments:
        parentScope = True
        arguments.pop()
    if arguments:
        # Retrieve or create node for each argument
        node = vmodel.expand(arguments)
    else:  # SET (VAR) // Removes the definition of VAR.
        lookupTable.deleteKey(variable_name)
        return
    # Each variable has its own RefNode
    variableNode = RefNode("{}_{}".format(variable_name, vmodel.getNextCounter()), node)

    # If inside condition, we just create a SelectNode after newly created RefNode which true edge points to the new
    # node created for the arguments. If the variable were already defined before the if, the false edge
    # points to that
    systemState = None
    stateProperty = None
    if vmodel.getCurrentSystemState():
        systemState, stateProperty = vmodel.getCurrentSystemState()

    if systemState == 'if' or systemState == 'else' or systemState == 'elseif':
        selectNodeName = "SELECT_{}_{}_{}".format(variable_name,
                                                  util_getStringFromList(stateProperty), vmodel.getNextCounter())
        newSelectNode = SelectNode(selectNodeName, stateProperty)

        if systemState == 'if' or systemState == 'elseif':
            newSelectNode.setTrueNode(node)
        elif systemState == 'else':
            newSelectNode.setFalseNode(node)
        # Inside if statement, we set true node to the variable defined outside if which pushed
        # to this stack before entering the if statement
        if vmodel.getLastPushedLookupTable().getKey(variable_name):
            if systemState == 'if' or systemState == 'elseif':
                newSelectNode.setFalseNode(vmodel.getLastPushedLookupTable().getKey(variable_name))
            elif systemState == 'else':
                newSelectNode.setTrueNode(vmodel.getLastPushedLookupTable().getKey(variable_name))

        variableNode.pointTo = newSelectNode

    # Finally, we add the new RefNode to the graph and our lookup table
    vmodel.nodes.append(variableNode)
    lookupTable.setKey(variable_name, variableNode, parentScope)


def listCommand(arguments):
    # List command supports many actions, like APPEND, INSERT, ...
    action = arguments.pop(0)
    action = action.upper()
    listName = "${{{}}}".format(arguments.pop(0))
    listVariable = lookupTable.getKey(listName)

    if action == 'LENGTH':
        outVariable = "${{{}}}".format(arguments.pop(0))
        commandName = 'LIST.LENGTH'
        if commandName:
            commandName = commandName + "_" + vmodel.getNextCounter()
        command = CustomCommandNode(commandName)
        command.pointTo.append(listVariable)
        variable = RefNode("{}_{}".format(outVariable, vmodel.getNextCounter()), command)

        newNode = command
        newVModel = variable
        newName = outVariable

    if action == 'SORT' or action == 'REVERSE' or action == 'REMOVE_DUPLICATES':
        commandName = 'LIST.' + action
        if commandName:
            commandName = commandName + "_" + vmodel.getNextCounter()
        command = CustomCommandNode(commandName)
        command.pointTo.append(listVariable)
        variable = RefNode("{}_{}".format(listName, vmodel.getNextCounter()), command)

        newNode = command
        newVModel = variable
        newName = listName

    if action == 'REMOVE_AT' or action == 'REMOVE_ITEM' or action == 'INSERT':
        commandName = 'LIST.{}({})'.format(action, " ".join(arguments))
        if commandName:
            commandName = commandName + "_" + vmodel.getNextCounter()
        command = CustomCommandNode(commandName)
        command.pointTo.append(listVariable)
        variable = RefNode("{}_{}".format(listName, vmodel.getNextCounter()), command)

        newNode = command
        newVModel = variable
        newName = listName

    if action == 'FIND':
        valueToLook = arguments.pop(0)
        outVariable = "${{{}}}".format(arguments.pop(0))
        commandName = 'LIST.FIND({})'.format(valueToLook)
        if commandName:
            commandName = commandName + "_" + vmodel.getNextCounter()
        command = CustomCommandNode(commandName)
        command.pointTo.append(listVariable)

        variable = RefNode("{}_{}".format(outVariable, vmodel.getNextCounter()), command)

        newNode = command
        newVModel = variable
        newName = outVariable

    if action == 'GET':
        outVariable = "${{{}}}".format(arguments.pop())
        commandName = 'LIST.GET({})'.format(" ".join(arguments))
        if commandName:
            commandName = commandName + "_" + vmodel.getNextCounter()
        command = CustomCommandNode(commandName)
        command.pointTo.append(listVariable)

        variable = RefNode("{}_{}".format(outVariable, vmodel.getNextCounter()), command)

        newNode = command
        newVModel = variable
        newName = outVariable

    if action == 'APPEND':
        # We create a concatNode contains the arguments and a new RefNode for the variable
        concatNode = ConcatNode("LIST_" + listName + ",".join(arguments) + vmodel.getNextCounter())
        listVModel = RefNode("{}_{}".format(listName, vmodel.getNextCounter()), concatNode)

        argumentSet = vmodel.flatten(arguments)
        for item in argumentSet:
            concatNode.addNode(item)

        # Now we check if this variable were previously defined
        prevListVar = lookupTable.getKey(listName)
        if prevListVar:
            concatNode.addToBeginning(prevListVar)

        newNode = concatNode
        newVModel = listVModel
        newName = listName

    systemState = None
    stateProperty = None
    if vmodel.getCurrentSystemState():
        systemState, stateProperty = vmodel.getCurrentSystemState()

    if systemState == 'if' or systemState == 'else' or systemState == 'elseif':
        selectNodeName = "SELECT_{}_{}_{}".format(newName,
                                                  util_getStringFromList(stateProperty), vmodel.getNextCounter())
        newSelectNode = SelectNode(selectNodeName, stateProperty)

        if systemState == 'if' or systemState == 'elseif':
            newSelectNode.setTrueNode(newNode)
        elif systemState == 'else':
            newSelectNode.setFalseNode(newNode)
        # Inside if statement, we set true node to the variable defined outside if which pushed
        # to this stack before entering the if statement
        if vmodel.getLastPushedLookupTable().getKey(newName):
            if systemState == 'if' or systemState == 'elseif':
                newSelectNode.setFalseNode(vmodel.getLastPushedLookupTable().getKey(newName))
            elif systemState == 'else':
                newSelectNode.setTrueNode(vmodel.getLastPushedLookupTable().getKey(newName))

        newVModel.pointTo = newSelectNode

    lookupTable.setKey(newName, newVModel)
    vmodel.nodes.append(newVModel)


def whileCommand(arguments):
    customCommand = CustomCommandNode("WHILE({})".format(util_getStringFromList(arguments)))
    vmodel.pushSystemState('while', customCommand)
    vmodel.pushCurrentLookupTable()


# We compare lookup table before while and after that. For any changed variable, or newly created one,
# the tool will add the RefNode to the while command node, then it creates a new RefNode pointing to the
# While command node
def endwhileCommand():
    lastPushedLookup = vmodel.getLastPushedLookupTable()
    state, command = vmodel.popSystemState()
    for key in lookupTable.items[-1].keys():
        if key not in lastPushedLookup.items[-1].keys() or lookupTable.getKey(key) != lastPushedLookup.getKey(key):
            command.pointTo.append(lookupTable.getKey(key))
            refNode = RefNode("{}_{}".format(key, vmodel.getNextCounter()), command)
            lookupTable.setKey(key, refNode)
            vmodel.nodes.append(refNode)


def fileCommand(arguments):
    action = arguments.pop(0)
    fileCommandNode = None
    if action in ('WRITE', 'APPEND'):
        fileName = arguments.pop(0)
        fileNode = vmodel.expand([fileName])
        contents = vmodel.expand(arguments)
        fileCommandNode = CustomCommandNode("FILE.({} {})_{}".format(action, fileName, vmodel.getNextCounter()))
        fileCommandNode.pointTo.append(fileNode)
        fileCommandNode.pointTo.append(contents)

    elif action in ('READ', 'STRINGS', 'MD5', 'SHA1', 'SHA224', 'SHA256', 'SHA384', 'SHA512'):
        fileName = arguments.pop(0)
        fileNode = vmodel.expand([fileName])
        variableName = arguments.pop(0)
        fileCommandNode = CustomCommandNode("FILE.({} {} {})_{}".format(action, fileName,
                                                                        " ".join(arguments), vmodel.getNextCounter()))
        fileCommandNode.pointTo.append(fileNode)
        refNode = RefNode("{}_{}".format(variableName, vmodel.getNextCounter()), fileCommandNode)
        lookupTable.setKey("${{{}}}".format(variableName), refNode)
        vmodel.nodes.append(refNode)

    elif action in ('GLOB', 'GLOB_RECURSE'):
        variableName = arguments.pop(0)
        fileCommandNode = CustomCommandNode("FILE.({})_{}".format(action, vmodel.getNextCounter()))
        fileCommandNode.pointTo.append(vmodel.expand(arguments))
        refNode = RefNode("{}_{}".format(variableName, vmodel.getNextCounter()), fileCommandNode)
        lookupTable.setKey("${{{}}}".format(variableName), refNode)
        vmodel.nodes.append(refNode)

    elif action in ('REMOVE', 'REMOVE_RECURSE', 'MAKE_DIRECTORY'):
        fileCommandNode = CustomCommandNode("FILE.({})_{}".format(action, vmodel.getNextCounter()))
        fileCommandNode.pointTo.append(vmodel.expand(arguments))


    vmodel.nodes.append(fileCommandNode)


# Current strategy for foreach loop does not support nested foreach! If this is a case, we should change
# create a activation record style class for each foreach command
forEachVariableName = None
forEachArguments = []
forEachCommands = []


def forEachCommand(arguments):
    global forEachVariableName
    global forEachArguments
    forEachVariableName = "${{{}}}".format(arguments.pop(0))
    forEachArguments = arguments
    vmodel.enableRecordCommands()


def processCommand(commandId, args):
    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get("{}Command".format(commandId))
    if not method:
        raise NotImplementedError("Method %s not implemented" % commandId)
    method(args)


class CMakeExtractorListener(CMakeListener):
    def __init__(self):
        global vmodel
        global lookupTable
        vmodel = VModel.getInstance()
        lookupTable = Lookup.getInstance()

    def enterSetCommand(self, ctx: CMakeParser.SetCommandContext):
        # Extract arguments
        arguments = [child.getText() for child in ctx.argument().getChildren() if not isinstance(child, TerminalNode)]
        if vmodel.shouldRecordCommand():
            forEachCommands.append(('set', arguments))
        elif vmodel.currentFunctionCommand is not None:
            vmodel.currentFunctionCommand.append(('set', arguments))
        else:
            setCommand(arguments)

    def enterIfCommand(self, ctx: CMakeParser.IfCommandContext):
        vmodel.setInsideIf()
        vmodel.pushCurrentLookupTable()
        vmodel.ifConditions.append(" ".join([argument.getText() for argument in ctx.ifStatement().argument().children if
                                             not isinstance(argument, TerminalNode)]))

        vmodel.pushSystemState('if', ([argument.getText() for argument in ctx.ifStatement().argument().children]))

    def enterElseIfStatement(self, ctx: CMakeParser.ElseIfStatementContext):
        vmodel.popLookupTable()
        vmodel.pushCurrentLookupTable()
        state, condition = vmodel.getCurrentSystemState()
        # We create a new condition list. Add previous condition (which drives from and if or prev else if)
        # and NOT it and AND it with our condition. This new list will later be parsed to evaluate the query.
        # We keep previous condition for else statement
        condition = ['((', 'NOT'] + condition + [')', 'AND'] + [argument.getText() for argument in
                                                                ctx.argument().children] + [')']
        vmodel.pushSystemState('elseif', condition)

    def enterElseStatement(self, ctx: CMakeParser.ElseStatementContext):
        # We create a new condition list which in a <CONDITION_1 or CONDITION_2 or ...> format
        elseCondition = []
        while True:
            state, condition = vmodel.getCurrentSystemState()
            elseCondition += condition
            if state != 'if':
                vmodel.popSystemState()
                elseCondition.append('OR')
            else:
                vmodel.popSystemState()
                break

        vmodel.popLookupTable()
        vmodel.pushCurrentLookupTable()
        vmodel.pushSystemState('else', elseCondition)

    def exitIfCommand(self, ctx: CMakeParser.IfCommandContext):
        vmodel.setOutsideIf()
        vmodel.ifConditions.pop()
        vmodel.popLookupTable()
        vmodel.popSystemState()

    def enterAdd_custom_command(self, ctx: CMakeParser.Add_custom_commandContext):
        dependedElement: List[TargetNode] = []
        # Check if we have depend command
        for item in ctx.otherArg:
            if item.argType.text == 'DEPENDS':
                for targetValue in item.argValue:
                    targetElement = vmodel.findNode(targetValue.getText())
                    if targetElement is not None:
                        # raise Exception("This should not happen! NOT_IMPLEMENTED")
                        dependedElement.append(targetElement)

        # Currently we only support one dependency
        if len(dependedElement) > 1:
            raise Exception("NOT_IMPLEMENTED")

        customCommandNode = CustomCommandNode("\n".join([cmd.getText() for cmd in ctx.command]))
        if dependedElement:
            customCommandNode.pointTo = dependedElement[0]

        for item in ctx.output:
            if vmodel.findNode(item.getText()):
                raise Exception('NOT_IMPLEMENTED')

            variableNode = RefNode(item.getText(), customCommandNode)
            vmodel.addNode(variableNode)

    def enterAdd_test_command(self, ctx: CMakeParser.Add_test_commandContext):
        targetNode = vmodel.findNode(ctx.test_command[0].getText())
        testNode = TestNode("TEST_" + ctx.test_name.getText(), targetNode)
        vmodel.addNode(testNode)

    def enterOptionCommand(self, ctx: CMakeParser.OptionCommandContext):
        arguments = [child.getText() for child in ctx.argument().getChildren() if not isinstance(child, TerminalNode)]
        optionName = arguments.pop(0)
        optionInitialValue = False
        if len(arguments) > 1:
            arguments.pop(0)  # Remove description from the option command
            optionInitialValue = arguments.pop(0)
        vmodel.addOption(optionName, optionInitialValue)

    def enterCommand_invocation(self, ctx: CMakeParser.Command_invocationContext):
        global project_dir
        commandId = ctx.Identifier().getText().lower()
        arguments = [child.getText() for child in ctx.argument().getChildren() if not isinstance(child, TerminalNode)]
        if commandId == 'set':
            raise Exception("This should not reach to this code!!!")

        elif commandId == 'function':
            functionName = arguments.pop(0)
            vmodel.functions[functionName] = {'arguments': arguments, 'commands': []}
            vmodel.currentFunctionCommand = vmodel.functions[functionName]['commands']

        elif commandId == 'endfunction':
            vmodel.currentFunctionCommand = None

        elif commandId == 'while':
            whileCommand(arguments)

        elif commandId == 'endwhile':
            endwhileCommand()

        elif commandId == 'unset':
            variable_name = "${{{}}}".format(arguments.pop(0))
            parentScope = False
            if "PARENT_SCOPE" in arguments:
                parentScope = True
            lookupTable.deleteKey(variable_name, parentScope)

        elif commandId == 'foreach':
            forEachCommand(arguments)

        elif commandId == 'endforeach':
            vmodel.disableRecordCommands()

            # Whether we should use range mode or continue as variables
            if 'RANGE' in forEachArguments:
                start = 0
                step = 1
                # single number, the range will have elements 0 to “total”.
                if len(forEachArguments) == 2:
                    stop = forEachArguments[1]
                elif len(forEachArguments) == 3:
                    start = forEachArguments[1]
                    stop = forEachArguments[2]
                elif len(forEachArguments) == 4:
                    start = forEachArguments[1]
                    stop = forEachArguments[2]
                    step = forEachArguments[3]
                for index in range(start, stop, step):
                    for commandType, commandArgs in forEachCommands:
                        newArgs = [i.replace(forEachVariableName, index) for i in commandArgs]
                        processCommand(commandType, newArgs)
            elif 'IN' in forEachArguments:
                forEachArguments.pop(0)
                while forEachArguments:
                    type = forEachArguments.pop(0)
                    if type == 'LISTS':
                        while forEachArguments and forEachArguments[0] != 'ITEMS':
                            listName = forEachArguments.pop(0)
                            # variableObject = lookupTable.getKey('${{{}}}'.format(listName))
                            # possibleValues = variableObject.getTerminalNodes()
                            # for item in possibleValues:
                            #     for commandType, commandArgs in forEachCommands:
                            #         newArgs = [i.replace(forEachVariableName, item.getValue()) for i in commandArgs]
                            #         processCommand(commandType, newArgs)
                            listFullName = '${{{}}}'.format(listName)
                            for commandType, commandArgs in forEachCommands:
                                newArgs = [i.replace(forEachVariableName, listFullName) for i in commandArgs]
                                processCommand(commandType, newArgs)
                    if type == 'ITEMS':
                        while forEachArguments:
                            item = forEachArguments.pop(0)
                            for commandType, commandArgs in forEachCommands:
                                newArgs = [i.replace(forEachVariableName, item) for i in commandArgs]
                                processCommand(commandType, newArgs)

            else:
                for arg in forEachArguments:
                    for commandType, commandArgs in forEachCommands:
                        newArgs = [i.replace(forEachVariableName, arg) for i in commandArgs]
                        processCommand(commandType, newArgs)

        elif commandId == 'add_subdirectory':
            tempProjectDir = project_dir
            project_dir = os.path.join(project_dir, ctx.argument().single_argument()[0].getText())
            parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
            project_dir = tempProjectDir

        elif commandId == 'add_library':
            targetName = arguments.pop(0)
            scope = None
            if arguments[0] in ('STATIC', 'SHARED', 'MODULE'):
                scope = arguments.pop(0)
            nextNode = vmodel.expand(arguments)
            targetNode = TargetNode(targetName, nextNode)
            targetNode.scope = scope
            vmodel.addNode(targetNode)

        elif commandId == 'add_executable':
            targetName = arguments.pop(0)
            nextNode = vmodel.expand(arguments)
            targetNode = lookupTable.getKey('t:{}'.format(targetName))
            if targetNode is None:
                targetNode = TargetNode(targetName, nextNode)
                targetNode.setDefinition(vmodel.COMPILE_OPTIONS)
                lookupTable.setKey('t:{}'.format(targetName), targetNode)
                vmodel.nodes.append(targetNode)

            systemState = None
            stateProperty = None
            if vmodel.getCurrentSystemState():
                systemState, stateProperty = vmodel.getCurrentSystemState()

            if systemState == 'if' or systemState == 'else' or systemState == 'elseif':
                selectNodeName = "SELECT_{}_{}_{}".format(targetName,
                                                          util_getStringFromList(stateProperty),
                                                          vmodel.getNextCounter())
                newSelectNode = SelectNode(selectNodeName, stateProperty)

                if systemState == 'if' or systemState == 'elseif':
                    newSelectNode.setTrueNode(nextNode)
                elif systemState == 'else':
                    newSelectNode.setFalseNode(nextNode)
                # Inside if statement, we set true node to the variable defined outside if which pushed
                # to this stack before entering the if statement
                if vmodel.getLastPushedLookupTable().getKey('t:{}'.format(targetName)):
                    if systemState == 'if' or systemState == 'elseif':
                        newSelectNode.setFalseNode(
                            vmodel.getLastPushedLookupTable().getKey('t:{}'.format(targetName)).getPointTo())
                    elif systemState == 'else':
                        newSelectNode.setTrueNode(
                            vmodel.getLastPushedLookupTable().getKey('t:{}'.format(targetName)).getPointTo())

                targetNode.pointTo = newSelectNode

        elif commandId == 'list':
            if vmodel.shouldRecordCommand():
                forEachCommands.append(('list', arguments))
            else:
                listCommand(arguments)

        elif commandId == 'file':
            fileCommand(arguments)

        elif commandId == 'target_include_directories':
            pass

        elif commandId == 'add_compile_options':
            nextNode = vmodel.expand(arguments)
            targetNode = nextNode

            systemState = None
            stateProperty = None
            if vmodel.getCurrentSystemState():
                systemState, stateProperty = vmodel.getCurrentSystemState()

            if systemState == 'if' or systemState == 'else' or systemState == 'elseif':
                selectNodeName = "SELECT_{}_{}_{}".format(nextNode.name,
                                                          util_getStringFromList(stateProperty),
                                                          vmodel.getNextCounter())
                newSelectNode = SelectNode(selectNodeName, stateProperty)

                if systemState == 'if' or systemState == 'elseif':
                    newSelectNode.setTrueNode(nextNode)
                elif systemState == 'else':
                    newSelectNode.setFalseNode(nextNode)
                # Inside if statement, we set true node to the variable defined outside if which pushed
                # to this stack before entering the if statement

                targetNode = newSelectNode

            newCompileOptions = ConcatNode("COMPILE_OPTIONS_{}".format(vmodel.getNextCounter()))
            if vmodel.COMPILE_OPTIONS:
                newCompileOptions.listOfNodes = list(vmodel.COMPILE_OPTIONS.listOfNodes)
            vmodel.COMPILE_OPTIONS = newCompileOptions
            vmodel.COMPILE_OPTIONS.addNode(targetNode)


        elif commandId == 'target_compile_definitions':
            # This command add a definition to the current ones. So we should add it in all the possible paths
            targetName = arguments.pop(0)
            scope = None
            targetNode = vmodel.findNode(targetName)
            if arguments[0] in ('INTERFACE', 'PUBLIC', 'PRIVATE'):
                scope = arguments.pop(0)
            nextNode = vmodel.expand(arguments)
            if scope:
                nextNode.name = scope + "_" + nextNode.name
            # vmodel.addNode(nextNode)
            if vmodel.isInsideIf():
                if targetNode.definitions is not None:
                    # TODO: Should create a select node and set the true edge
                    raise Exception('NOT_IMPLEMENTED')

                newSelectNode = SelectNode(targetName + "_DEFINITIONS", vmodel.ifConditions)
                newSelectNode.trueNode = nextNode
                newSelectNode.falseNode = targetNode.getDefinition()
                targetNode.setDefinition(newSelectNode)
            else:
                if targetNode.definitions is None:
                    targetNode.setDefinition(nextNode)
                else:
                    if isinstance(targetNode.getDefinition(), ConcatNode):
                        targetNode.getDefinition().addNode(nextNode)
                    if isinstance(targetNode.getDefinition(), SelectNode):
                        if targetNode.getDefinition().trueNode:
                            targetNode.getDefinition().trueNode = vmodel.convertOrGetConcatNode(
                                targetNode.getDefinition().trueNode)
                            targetNode.getDefinition().trueNode.addNode(nextNode)
                        else:
                            targetNode.getDefinition().trueNode = nextNode

                        if targetNode.getDefinition().falseNode:
                            targetNode.getDefinition().falseNode = vmodel.convertOrGetConcatNode(
                                targetNode.getDefinition().falseNode)
                            targetNode.getDefinition().falseNode.addNode(nextNode)
                        else:
                            targetNode.getDefinition().falseNode = nextNode

        elif commandId == 'target_link_libraries':
            targetName = arguments.pop(0)
            scope = None
            targetNode = vmodel.findNode(targetName)
            if arguments[0] in ('INTERFACE', 'PUBLIC', 'PRIVATE'):
                scope = arguments.pop(0)

            linkLibraries = None
            argumentSet = vmodel.flatten(arguments)
            if len(argumentSet) > 1:
                linkLibraries = ConcatNode("CONCAT_" + ",".join(argumentSet))
                for target in argumentSet:
                    node = vmodel.findNode(target)
                    # Linking to an external library
                    if node is None:
                        node = RefNode(target, None)
                    linkLibraries.addNode(node)
            else:
                linkLibraries = vmodel.findNode(argumentSet.pop())

            if vmodel.isInsideIf():
                newSelectNode = SelectNode(targetName + "_LIBRARIES", vmodel.ifConditions)
                newSelectNode.trueNode = linkLibraries
                newSelectNode.falseNode = targetNode.linkLibraries
                targetNode.linkLibraries = newSelectNode
            else:
                targetNode.linkLibraries = linkLibraries

        else:
            customFunction = vmodel.functions.get(commandId)
            if customFunction is None:
                raise Exception('unknown command!')
            vmodel.lookupTable.newScope()
            functionArguments = customFunction.get('arguments')
            for commandType, commandArgs in customFunction.get('commands'):
                for arg in functionArguments:
                    newArgs = [args.replace("${{{}}}".format(arg), arguments[functionArguments.index(arg)])
                               for args in commandArgs]
                    processCommand(commandType, newArgs)
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


def main(argv):
    global project_dir
    project_dir = argv[1]
    parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
    vmodel.checkIntegrity()
    vmodel.export(False)
    # !!!!!!!!!!!!!! This is for test
    # targetNode = vmodel.findNode("zlib")
    # sampleFile = vmodel.findNode("contrib/masmx86/inffas32.asm")
    # conditions = {"(MSVC)" : True, "(ASM686)": False}
    # vmodel.pathWithCondition(targetNode, sampleFile, **conditions)
    # !!!!!!!!!!!!!! Until here
    # vmodel.findAndSetTargets()
    # doGitAnalysis(project_dir)


if __name__ == "__main__":
    main(sys.argv)
