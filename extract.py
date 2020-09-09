# Bultin Libraries
import sys
import os
import code
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
    CustomCommandNode, TestNode, LiteralNode, flattenAlgorithm, Node, OptionNode, flattenAlgorithmWithConditions
from analyze import printSourceFiles, printFilesForATarget, checkForCyclesAndPrint
from analyze import printInputVariablesAndOptions

config.DATABASE_URL = 'bolt://neo4j:123@localhost:7687'

project_dir = ""

vmodel = VModel.getInstance()
lookupTable = Lookup.getInstance()


def util_getStringFromList(lst: List):
    return " ".join(lst)


def util_extract_variable_name(argName: str, arguments: List) -> Optional[str]:
    if argName in arguments:
        argIndex = arguments.index(argName)
        arguments.pop(argIndex)
        return arguments.pop(argIndex)
    return None


def util_create_and_add_refNode_for_variable(varName: str, nextNode: Node,
                                             parentScope=False, relatedProperty=None) -> RefNode:
    variable_name = "${{{}}}".format(varName)
    # Each variable has its own RefNode
    variableNode = RefNode("{}".format(variable_name), nextNode)
    if relatedProperty:
        variableNode.relatedProperty = relatedProperty

    variableNode.pointTo = util_handleConditions(nextNode, variable_name)

    # Finally, we add the new RefNode to the graph and our lookup table
    vmodel.nodes.append(variableNode)
    lookupTable.setKey(variable_name, variableNode, parentScope)
    return variableNode


# This function looks for previously defined node in the lookup table which works for variables and targets, but
# not for other nodes that we don't push to lookup table. This third argument helps to manually pass that node.
def util_handleConditions(nextNode, newNodeName, prevNode=None):
    # If inside condition, we just create a SelectNode after newly created RefNode (Node)
    # which true edge points to the new node created for the arguments.
    # If the variable were already defined before the if, the false edge points to that
    systemState = None
    stateProperty = None

    # The for statement will traverse all nested if nodes and create corresponding select node for each of them
    # However, we only interested in states in outer levels. So, we skip the ones in a same level
    # For example, in an if -> if | else scenario, when we are processing the else, we skip in inner most if
    currentIfLevel = 1000
    for systemState, stateProperty, level in reversed(vmodel.systemState):
        if currentIfLevel == level:
            continue
        currentIfLevel = min(currentIfLevel, level)
        if systemState == 'if' or systemState == 'else' or systemState == 'elseif':
            selectNodeName = "SELECT_{}_{}".format(newNodeName,
                                                   util_getStringFromList(stateProperty))
            newSelectNode = SelectNode(selectNodeName, stateProperty)
            newSelectNode.args = vmodel.expand(stateProperty)

            if systemState == 'if' or systemState == 'elseif':
                newSelectNode.setTrueNode(nextNode)
            elif systemState == 'else':
                newSelectNode.setFalseNode(nextNode)
            # Inside if statement, we set true node to the variable defined outside if which pushed
            # to this stack before entering the if statement
            if prevNode or vmodel.getLastPushedLookupTable().getKey(newNodeName):
                if systemState == 'if' or systemState == 'elseif':
                    newSelectNode.setFalseNode(prevNode or vmodel.getLastPushedLookupTable().getKey(newNodeName))
                elif systemState == 'else':
                    newSelectNode.setTrueNode(prevNode or vmodel.getLastPushedLookupTable().getKey(newNodeName))
            nextNode = newSelectNode
            # newNodeName = nextNode.name

    return nextNode


def setCommand(arguments):
    rawVarName = arguments.pop(0)
    variable_name = "${{{}}}".format(rawVarName)
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
    util_create_and_add_refNode_for_variable(rawVarName, node, parentScope)


def listCommand(arguments):
    # List command supports many actions, like APPEND, INSERT, ...
    action = arguments.pop(0)
    action = action.upper()
    rawListName = arguments.pop(0)
    listName = "${{{}}}".format(rawListName)
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

        variable = RefNode(outVariable, command)

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

        variable = RefNode(outVariable, command)

        newNode = command
        newVModel = variable
        newName = outVariable

    if action == 'APPEND':
        # We create a concatNode contains the arguments and a new RefNode for the variable
        concatNode = ConcatNode("LIST_" + listName + ",".join(arguments))
        # listVModel = RefNode(listName, concatNode)

        argumentSet = vmodel.flatten(arguments)
        for item in argumentSet:
            concatNode.addNode(item)

        # Now we check if this variable were previously defined
        prevListVar = lookupTable.getKey(listName)
        if prevListVar:
            concatNode.addToBeginning(prevListVar)

        listVModel = util_create_and_add_refNode_for_variable(rawListName, concatNode)

        # newNode = concatNode
        # newVModel = listVModel
        # newName = listName
        return

    systemState = None
    stateProperty = None
    if vmodel.getCurrentSystemState():
        systemState, stateProperty, level = vmodel.getCurrentSystemState()

    if systemState == 'if' or systemState == 'else' or systemState == 'elseif':
        selectNodeName = "SELECT_{}_{}".format(newName,
                                               util_getStringFromList(stateProperty))
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
    # We want to show the dependency between while command and newly created nodes. We compare nodes before and after
    # while loop and connect while command node to them.
    vmodel.nodeStack.append(list(vmodel.nodes))


# We compare lookup table before while and after that. For any changed variable, or newly created one,
# the tool will add the RefNode to the while command node, then it creates a new RefNode pointing to the
# While command node
def endwhileCommand():
    lastPushedLookup = vmodel.getLastPushedLookupTable()
    state, command, level = vmodel.popSystemState()
    prevNodeStack = vmodel.nodeStack.pop()
    for item in vmodel.nodes:
        if item not in prevNodeStack:
            command.pointTo.append(item)
    for key in lookupTable.items[-1].keys():
        if key not in lastPushedLookup.items[-1].keys() or lookupTable.getKey(key) != lastPushedLookup.getKey(key):
            # command.pointTo.append(lookupTable.getKey(key))
            refNode = RefNode("{}_{}".format(key, vmodel.getNextCounter()), command)
            lookupTable.setKey(key, refNode)
            vmodel.nodes.append(refNode)


# 1- Create a custom command node for file command
# 2- Write the action (WRITE APPEND ...) as the first argument on the name of the node (e.g FILE(APPEND))
# 3- If file command mutate or define any variable, create a RefNode for that variable pointing to the file node
# 4- Any other argument given to the file command will be expanded (as it may have a variable which needs to be
# de-addressed) and added as child node to custom command node point to property

def fileCommand(arguments):
    action = arguments.pop(0)
    fileCommandNode = None
    if action in ('WRITE', 'APPEND'):
        fileName = arguments.pop(0)
        fileNode = vmodel.expand([fileName])
        contents = vmodel.expand(arguments)
        fileCommandNode = CustomCommandNode("FILE.({} {})".format(action, fileName))
        fileCommandNode.pointTo.append(fileNode)
        fileCommandNode.pointTo.append(contents)

    elif action in ('READ', 'STRINGS', 'MD5', 'SHA1', 'SHA224', 'SHA256', 'SHA384', 'SHA512', 'TIMESTAMP'):
        variableName = arguments.pop(1)
        fileCommandNode = CustomCommandNode("FILE.({})".format(action))
        fileCommandNode.pointTo.append(vmodel.expand(arguments))
        refNode = RefNode("{}".format(variableName), fileCommandNode)
        lookupTable.setKey("${{{}}}".format(variableName), refNode)
        vmodel.nodes.append(refNode)

    elif action in ('GLOB', 'GLOB_RECURSE', 'RELATIVE_PATH'):
        variableName = arguments.pop(0)
        fileCommandNode = CustomCommandNode("FILE")
        fileCommandNode.commands.append(vmodel.expand([action] + arguments))
        refNode = RefNode("{}".format(variableName), fileCommandNode)
        lookupTable.setKey("${{{}}}".format(variableName), refNode)
        vmodel.nodes.append(refNode)

    elif action in ('REMOVE', 'REMOVE_RECURSE', 'MAKE_DIRECTORY'):
        fileCommandNode = CustomCommandNode("FILE.({})".format(action))
        fileCommandNode.pointTo.append(vmodel.expand(arguments))

    elif action in ('TO_CMAKE_PATH', 'TO_NATIVE_PATH'):
        pathText = arguments.pop(0)
        variableName = arguments.pop(0)
        fileCommandNode = CustomCommandNode("FILE.({})".format(action))
        fileCommandNode.pointTo.append(vmodel.expand([pathText]))
        refNode = RefNode("{}".format(variableName), fileCommandNode)
        lookupTable.setKey("${{{}}}".format(variableName), refNode)
        vmodel.nodes.append(refNode)

    elif action in ('DOWNLOAD', 'UPLOAD', 'COPY', 'INSTALL'):
        # TODO: There is a "log" option for download and upload
        #  which takes a variable. Currently we ignore that specific option
        fileCommandNode = CustomCommandNode("FILE.({})".format(action))
        fileCommandNode.pointTo.append(vmodel.expand(arguments))

    elif action == 'GENERATE':
        # In cmake documentation (https://cmake.org/cmake/help/v3.1/command/file.html) there is only one possible
        # word after GENERATE which is OUTPUT. So I assume that the full action name is GENERATE OUTPUT
        arguments.pop(0)
        fileCommandNode = CustomCommandNode("FILE.(GENERATE OUTPUT)")
        fileCommandNode.pointTo.append(vmodel.expand(arguments))

    fileCommandNode.extraInfo['pwd'] = project_dir
    vmodel.nodes.append(fileCommandNode)


def addCompileOptionsCommand(arguments):
    nextNode = vmodel.expand(arguments)
    targetNode = util_handleConditions(nextNode, nextNode.name, None)

    newCompileOptions = ConcatNode("COMPILE_OPTIONS_{}".format(vmodel.getNextCounter()))
    if vmodel.DIRECTORY_PROPERTIES.getOwnKey('COMPILE_OPTIONS'):
        newCompileOptions.listOfNodes = list(vmodel.DIRECTORY_PROPERTIES.getKey('COMPILE_OPTIONS').listOfNodes)

    vmodel.DIRECTORY_PROPERTIES.setKey('COMPILE_OPTIONS', newCompileOptions)
    newCompileOptions.addNode(targetNode)


def addLinkLibraries(arguments):
    nextNode = vmodel.expand(arguments)
    targetNode = util_handleConditions(nextNode, nextNode.name, None)

    newLinkLibraries = ConcatNode("LINK_LIBRARIES_{}".format(vmodel.getNextCounter()))
    if vmodel.DIRECTORY_PROPERTIES.getOwnKey('LINK_LIBRARIES'):
        newLinkLibraries.listOfNodes = list(vmodel.DIRECTORY_PROPERTIES.getKey('LINK_LIBRARIES').listOfNodes)

    vmodel.DIRECTORY_PROPERTIES.setKey('LINK_LIBRARIES', newLinkLibraries)
    newLinkLibraries.addNode(targetNode)


def addLinkDirectories(arguments):
    nextNode = vmodel.expand(arguments)
    targetNode = util_handleConditions(nextNode, nextNode.name, None)

    newLinkDirectories = ConcatNode("LINK_DIRECTORIES_{}".format(vmodel.getNextCounter()))
    if vmodel.DIRECTORY_PROPERTIES.getOwnKey('LINK_DIRECTORIES'):
        newLinkDirectories.listOfNodes = list(vmodel.DIRECTORY_PROPERTIES.getKey('LINK_DIRECTORIES').listOfNodes)

    vmodel.DIRECTORY_PROPERTIES.setKey('LINK_DIRECTORIES', newLinkDirectories)
    newLinkDirectories.addNode(targetNode)


# This function handles both add_library and add_executable
def addTarget(arguments, isExecutable=True):
    targetName = arguments.pop(0)
    lookupTableName = 't:{}'.format(targetName)
    nextNode = None
    libraryType = None
    isObjectLibrary = False
    interfaceLibrary = None

    # These values may exist in add_library only. There is a type property in TargetNode that we can set
    if arguments[0] in ('STATIC', 'SHARED', 'MODULE'):
        libraryType = arguments.pop(0)

    # Object libraries just contains list of files, so there is small change in behaviour
    if arguments[0] == 'OBJECT':
        arguments.pop(0)
        isObjectLibrary = True
        lookupTableName = "$<TARGET_OBJECTS:{}>".format(targetName)

    # Interface libraries are useful for header-only libraries.
    # more info at: http://mariobadr.com/creating-a-header-only-library-with-cmake.html
    if arguments[0] == 'INTERFACE':
        arguments.pop(0)
        interfaceLibrary = True

    # IMPORTED target node doesn't have any more argument to expand
    # ALIAS target node points to another target node, so the logic behind it is a little different
    if arguments[0] not in ('IMPORTED', 'ALIAS'):
        nextNode = vmodel.expand(arguments, True)

    targetNode = lookupTable.getKey(lookupTableName)
    if targetNode is None:
        targetNode = TargetNode(targetName, nextNode)
        targetNode.setDefinition(vmodel.DIRECTORY_PROPERTIES.getKey('COMPILE_OPTIONS'))
        targetNode.linkLibraries = vmodel.DIRECTORY_PROPERTIES.getKey('LINK_LIBRARIES')
        targetNode.includeDirectories = vmodel.DIRECTORY_PROPERTIES.getKey('INCLUDE_DIRECTORIES')
        lookupTable.setKey(lookupTableName, targetNode)
        vmodel.nodes.append(targetNode)

    if libraryType:
        targetNode.libraryType = libraryType

    targetNode.isExecutable = isExecutable
    targetNode.isObjectLibrary = isObjectLibrary
    targetNode.interfaceLibrary = interfaceLibrary

    # TODO: We have to decide whether keep the experiment to change it
    # EXPERIMENT: We flatten the target name and add all the possible values to the graph as a potential target
    flattedTargetName = flattenAlgorithmWithConditions(vmodel.expand([targetName]))
    if flattedTargetName:
        for item in flattedTargetName:
            # We already set a key with the name targetNode
            if item[0] != targetName:
                lookupTable.setKey("t:{}".format(item[0]), targetNode)


    if 'IMPORTED' in arguments:
        targetNode.imported = True

    if 'ALIAS' in arguments:
        aliasTarget = lookupTable.getKey('t:{}'.format(arguments[1]))
        targetNode.sources = aliasTarget

    systemState = None
    stateProperty = None
    if vmodel.getCurrentSystemState():
        systemState, stateProperty, level = vmodel.getCurrentSystemState()

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
        if vmodel.getLastPushedLookupTable().getKey(lookupTableName):
            if systemState == 'if' or systemState == 'elseif':
                newSelectNode.setFalseNode(
                    vmodel.getLastPushedLookupTable().getKey(lookupTableName).getPointTo())
            elif systemState == 'else':
                newSelectNode.setTrueNode(
                    vmodel.getLastPushedLookupTable().getKey(lookupTableName).getPointTo())

        targetNode.sources = newSelectNode


# Very similar to while command
def forEachCommand(arguments):
    customCommand = CustomCommandNode("foreach_{}".format(vmodel.getNextCounter()))
    customCommand.commands.append(vmodel.expand(arguments))
    vmodel.pushSystemState('foreach', customCommand)
    vmodel.pushCurrentLookupTable()
    # We want to show the dependency between foreach command and newly created nodes. We compare nodes before and after
    # while loop and connect while command node to them.
    vmodel.nodeStack.append(list(vmodel.nodes))


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

    def enterIfCommand(self, ctx: CMakeParser.IfCommandContext):
        vmodel.setInsideIf()
        vmodel.pushCurrentLookupTable()
        vmodel.ifLevel += 1
        arguments = [argument.getText() for argument in ctx.ifStatement().argument().children if
                     not isinstance(argument, TerminalNode)]
        processedArgs = []

        reservedWords = [
            'NOT', 'AND', 'OR', 'COMMAND', 'POLICY', 'TARGET', 'EXISTS', 'IS_NEWER_THAN', 'IS_DIRECTORY',
            'IS_SYMLINK', 'IS_ABSOLUTE', 'MATCHES', 'LESS', 'GREATER', 'EQUAL', 'STRLESS', 'STRGREATER',
            'STREQUAL', 'VERSION_LESS', 'VERSION_EQUAL', 'VERSION_GREATER', 'DEFINED',
            'ON', 'OFF', 'YES', 'NO', 'TRUE', 'FALSE'
        ]
        vmodel.ifConditions.append(" ".join(arguments))
        for arg in [argument for argument in ctx.ifStatement().argument().children if
                    not isinstance(argument, TerminalNode)]:
            if arg.getChild(0).symbol.type == CMakeParser.Quoted_argument or \
                    arg.getText().upper() in reservedWords or \
                    arg.getText().isnumeric():
                processedArgs.append(arg.getText())
                # TODO: A temporary fix to create space between arguments. Otherwise, NOT will be followed by the arg
                #       without any space
                processedArgs.append(" ")
            else:
                processedArgs.append("${{{}}}".format(arg.getText()))

        vmodel.pushSystemState('if', processedArgs)

    def enterElseIfStatement(self, ctx: CMakeParser.ElseIfStatementContext):
        vmodel.popLookupTable()
        vmodel.pushCurrentLookupTable()
        state, condition, level = vmodel.getCurrentSystemState()

        reservedWords = [
            'NOT', 'AND', 'OR', 'COMMAND', 'POLICY', 'TARGET', 'EXISTS', 'IS_NEWER_THAN', 'IS_DIRECTORY',
            'IS_SYMLINK', 'IS_ABSOLUTE', 'MATCHES', 'LESS', 'GREATER', 'EQUAL', 'STRLESS', 'STRGREATER',
            'STREQUAL', 'VERSION_LESS', 'VERSION_EQUAL', 'VERSION_GREATER', 'DEFINED',
            'ON', 'OFF', 'YES', 'NO', 'TRUE', 'FALSE'
        ]
        elseIfCondition = []
        for arg in [argument for argument in ctx.argument().children if
                    not isinstance(argument, TerminalNode)]:
            if arg.getChild(0).symbol.type == CMakeParser.Quoted_argument or \
                    arg.getText().upper() in reservedWords or \
                    arg.getText().isnumeric():
                elseIfCondition.append(arg.getText())
            else:
                elseIfCondition.append("${{{}}}".format(arg.getText()))
        # We create a new condition list. Add previous condition (which drives from and if or prev else if)
        # and NOT it and AND it with our condition. This new list will later be parsed to evaluate the query.
        # We keep previous condition for else statement
        condition = ['((', 'NOT'] + condition + [')', 'AND'] + elseIfCondition + [')']
        vmodel.pushSystemState('elseif', condition)

    def enterElseStatement(self, ctx: CMakeParser.ElseStatementContext):
        # We create a new condition list which in a <CONDITION_1 or CONDITION_2 or ...> format
        elseCondition = []
        while True:
            state, condition, level = vmodel.getCurrentSystemState()
            elseCondition += condition
            if state != 'if':
                vmodel.popSystemState()
                elseCondition.append('OR')
            else:
                break

        vmodel.popLookupTable()
        vmodel.pushCurrentLookupTable()
        vmodel.pushSystemState('else', elseCondition)

    def exitIfCommand(self, ctx: CMakeParser.IfCommandContext):
        vmodel.setOutsideIf()
        vmodel.ifConditions.pop()
        vmodel.popLookupTable()
        vmodel.ifLevel -= 1
        # In case of an if statement without else command, the state of the if itself and multiple else ifs
        # still exists. We should keep popping until we reach to the if
        while True:
            state, condition, level = vmodel.popSystemState()
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
            addCompileOptionsCommand(arguments)

        # remove_definitions(-DFOO -DBAR ...)
        elif commandId == 'remove_definitions':
            fileNode = CustomCommandNode('remove_definitions')
            fileNode.commands.append(vmodel.expand(arguments))
            vmodel.nodes.append(util_handleConditions(fileNode, fileNode.name))

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

            systemState = None
            stateProperty = None
            if vmodel.getCurrentSystemState():
                systemState, stateProperty, level = vmodel.getCurrentSystemState()

            args = vmodel.expand(arguments)
            commandNode.depends.append(args)

            prevNodeStack = list(vmodel.nodes)
            # We execute the command if we can find the CMake file and there is no condition to execute it
            if os.path.exists(os.path.join(project_dir, args.getValue())):
                parseFile(os.path.join(project_dir, args.getValue()))
                for item in vmodel.nodes:
                    if item not in prevNodeStack:
                        commandNode.commands.append(item)
            else:
                print("No! : {}".format(arguments))
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
                    target.addLinkLibrary(customCommand, vmodel.getNextCounter())
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

            targetNode = TargetNode("{}_{}".format(targetName, vmodel.getNextCounter()), vmodel.expand(arguments))
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
            vmodel.nodes.append(commandNode)

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
            state, command, level = vmodel.popSystemState()
            forEachVariableName = command.commands[0].getChildren()[0].getValue()
            prevNodeStack = vmodel.nodeStack.pop()
            for item in vmodel.nodes:
                if item not in prevNodeStack:
                    command.depends.append(item)
            for key in lookupTable.items[-1].keys():
                if key not in lastPushedLookup.items[-1].keys() or \
                        lookupTable.getKey(key) != lastPushedLookup.getKey(key):
                    # We don't want to create a ref node for the variable that is the argument of foreach command
                    if key == "${{{}}}".format(forEachVariableName):
                        continue
                    refNode = RefNode("{}_{}".format(key, vmodel.getNextCounter()), command)
                    lookupTable.setKey(key, refNode)
                    vmodel.nodes.append(refNode)

        elif commandId == 'add_subdirectory':
            tempProjectDir = project_dir
            project_dir = os.path.join(project_dir, ctx.argument().single_argument()[0].getText())
            parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
            project_dir = tempProjectDir

        elif commandId == 'add_library':
            addTarget(arguments, False)

        elif commandId == 'add_executable':
            addTarget(arguments, True)

        elif commandId == 'list':
            listCommand(arguments)

        elif commandId == 'file':
            fileCommand(arguments)

        # target_include_directories( < target > [SYSTEM][BEFORE]
        #         < INTERFACE | PUBLIC | PRIVATE > [items1...]
        #       [ < INTERFACE | PUBLIC | PRIVATE > [items2...]...])
        elif commandId == 'target_include_directories':
            targetName = arguments.pop(0)
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

        elif commandId == 'add_compile_options':
            addCompileOptionsCommand(arguments)

        # link_libraries([item1 [item2 [...]]]
        #        [[debug|optimized|general] <item>] ...)
        elif commandId == 'link_libraries':
            addLinkLibraries(arguments)

        # link_directories(directory1 directory2 ...)
        elif commandId == 'link_directories':
            addLinkDirectories(arguments)

        elif commandId == 'target_compile_definitions':
            # This command add a definition to the current ones. So we should add it in all the possible paths
            targetName = arguments.pop(0)
            scope = None
            targetNode = lookupTable.getKey('t:{}'.format(targetName))
            assert isinstance(targetNode, TargetNode)
            nextNode = vmodel.expand(arguments)
            if scope:
                nextNode.name = scope + "_" + nextNode.name
            # vmodel.addNode(nextNode)
            targetNode.setDefinition(util_handleConditions(nextNode, nextNode, targetNode.getDefinition()))

        elif commandId == 'target_link_libraries':
            customCommand = CustomCommandNode('target_link_libraries')
            customCommand.commands.append(vmodel.expand(arguments))
            finalNode = util_handleConditions(customCommand, customCommand.name, None)
            # Next variable should have the target nodes itself or the name of targets
            targetList = flattenAlgorithmWithConditions(customCommand.commands[0].getChildren()[0])
            for target in targetList:
                targetNode = target[0]
                if not isinstance(targetNode, TargetNode):
                    targetNode = lookupTable.getKey("t:{}".format(targetNode))
                # Now we should have a TargetNode
                assert isinstance(targetNode, TargetNode)
                assert isinstance(target[1], set)
                targetNode.linkLibrariesConditions[finalNode] = target[1]

            vmodel.nodes.append(
                finalNode
            )

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
                customCommand = CustomCommandNode("{}_{}".format(commandId, vmodel.getNextCounter()))
                customCommand.commands.append(vmodel.expand(arguments))
                vmodel.nodes.append(util_handleConditions(customCommand, customCommand.getName()))
                return
            if not customFunction.get('isMacro'):
                vmodel.lookupTable.newScope()
            functionArguments = customFunction.get('arguments')
            for commandType, commandArgs in customFunction.get('commands'):
                for arg in functionArguments:
                    newArgs = [args.replace("${{{}}}".format(arg), arguments[functionArguments.index(arg)])
                               for args in commandArgs]
                    processCommand(commandType, newArgs)
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


def main(argv):
    global project_dir
    project_dir = argv[1]
    parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
    # vmodel.checkIntegrity()
    # vmodel.export(True, False)
    # vmodel.export(False, True)
    # !!!!!!!!!!!!!! This is for test
    # targetNode = vmodel.findNode("zlib")
    # sampleFile = vmodel.findNode("contrib/masmx86/inffas32.asm")
    # conditions = {"(MSVC)" : True, "(ASM686)": False}
    # vmodel.pathWithCondition(targetNode, sampleFile, **conditions)
    # !!!!!!!!!!!!!! Until here
    # vmodel.findAndSetTargets()
    # doGitAnalysis(project_dir)
    # code.interact(local=dict(globals(), **locals()))
    # printInputVariablesAndOptions(vmodel, lookupTable)
    # printSourceFiles(vmodel, lookupTable)
    stackList = []
    visited = []
    # a = checkForCyclesAndPrint(vmodel, lookupTable, lookupTable.getKey("t:etl"), visited, stackList)
    # print(a)
    # testNode = vmodel.findNode('${CLIENT_LIBRARIES}_662')
    # flattenAlgorithmWithConditions(testNode)
    a = printFilesForATarget(vmodel, lookupTable, 'etl', True)
    print(a)

if __name__ == "__main__":
    main(sys.argv)
