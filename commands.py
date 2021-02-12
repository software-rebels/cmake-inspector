from algorithms import flattenAlgorithmWithConditions
from datastructs import Lookup, CustomCommandNode, TargetNode, ConcatNode
from utils import *


def setCommand(arguments):
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()
    # TODO: @Farshad: Why you added this line?
    if len(arguments) == 1:
        arguments.append('')
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
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()

    action = arguments.pop(0)
    action = action.upper()
    rawListName = arguments.pop(0)
    listName = "${{{}}}".format(rawListName)
    listVariable = lookupTable.getKey(listName)

    if action == 'LENGTH':
        outVariable = arguments.pop(0)
        commandName = 'LIST.LENGTH'
        command = CustomCommandNode(commandName)
        command.depends.append(listVariable)

        util_create_and_add_refNode_for_variable(outVariable, command)

    elif action == 'SORT' or action == 'REVERSE' or action == 'REMOVE_DUPLICATES':
        commandName = 'LIST.' + action
        command = CustomCommandNode(commandName)
        command.depends.append(listVariable)

        util_create_and_add_refNode_for_variable(rawListName, command)

    elif action == 'REMOVE_AT' or action == 'REMOVE_ITEM' or action == 'INSERT':
        commandName = 'LIST.{}'.format(action)
        command = CustomCommandNode(commandName)
        command.depends.append(listVariable)

        command.commands.append(vmodel.expand(arguments))
        util_create_and_add_refNode_for_variable(rawListName, command)

    elif action == 'FIND':
        valueToLook = arguments.pop(0)
        outVariable = arguments.pop(0)
        commandName = 'LIST.FIND'.format(valueToLook)
        command = CustomCommandNode(commandName)

        command.commands.append(vmodel.expand([valueToLook]))
        command.depends.append(listVariable)

        util_create_and_add_refNode_for_variable(outVariable, command)

    elif action == 'GET':
        outVariable = arguments.pop()
        commandName = 'LIST.GET'
        command = CustomCommandNode(commandName)
        command.depends.append(listVariable)
        command.commands.append(vmodel.expand(arguments))

        util_create_and_add_refNode_for_variable(outVariable, command)

    elif action == 'APPEND':
        # We create a concatNode contains the arguments
        concatNode = ConcatNode("LIST_" + listName + ",".join(arguments))

        argumentSet = vmodel.flatten(arguments)
        for item in argumentSet:
            concatNode.addNode(item)

        # Now we check if this variable were previously defined
        prevListVar = lookupTable.getKey(listName)
        if prevListVar:
            concatNode.addToBeginning(prevListVar)

        # A new RefNode will point to this new concatNode
        util_create_and_add_refNode_for_variable(rawListName, concatNode)


def whileCommand(arguments):
    vmodel = VModel.getInstance()

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
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()

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

def fileCommand(arguments, project_dir):
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()

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
    vmodel = VModel.getInstance()

    nextNode = vmodel.expand(arguments)
    targetNode = util_handleConditions(nextNode, nextNode.name, None)

    newCompileOptions = ConcatNode("COMPILE_OPTIONS_{}".format(vmodel.getNextCounter()))
    if vmodel.DIRECTORY_PROPERTIES.getOwnKey('COMPILE_OPTIONS'):
        newCompileOptions.listOfNodes = list(vmodel.DIRECTORY_PROPERTIES.getKey('COMPILE_OPTIONS').listOfNodes)

    vmodel.DIRECTORY_PROPERTIES.setKey('COMPILE_OPTIONS', newCompileOptions)
    newCompileOptions.addNode(targetNode)


def addLinkLibraries(arguments):
    vmodel = VModel.getInstance()

    nextNode = vmodel.expand(arguments)
    targetNode = util_handleConditions(nextNode, nextNode.name, None)

    newLinkLibraries = ConcatNode("LINK_LIBRARIES_{}".format(vmodel.getNextCounter()))
    if vmodel.DIRECTORY_PROPERTIES.getOwnKey('LINK_LIBRARIES'):
        newLinkLibraries.listOfNodes = list(vmodel.DIRECTORY_PROPERTIES.getKey('LINK_LIBRARIES').listOfNodes)

    vmodel.DIRECTORY_PROPERTIES.setKey('LINK_LIBRARIES', newLinkLibraries)
    newLinkLibraries.addNode(targetNode)


def addLinkDirectories(arguments):
    vmodel = VModel.getInstance()

    nextNode = vmodel.expand(arguments)
    targetNode = util_handleConditions(nextNode, nextNode.name, None)

    newLinkDirectories = ConcatNode("LINK_DIRECTORIES_{}".format(vmodel.getNextCounter()))
    if vmodel.DIRECTORY_PROPERTIES.getOwnKey('LINK_DIRECTORIES'):
        newLinkDirectories.listOfNodes = list(vmodel.DIRECTORY_PROPERTIES.getKey('LINK_DIRECTORIES').listOfNodes)

    vmodel.DIRECTORY_PROPERTIES.setKey('LINK_DIRECTORIES', newLinkDirectories)
    newLinkDirectories.addNode(targetNode)


# This function handles both add_library and add_executable
def addTarget(arguments, isExecutable=True):
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()

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
    if arguments and arguments[0] == 'OBJECT':
        arguments.pop(0)
        isObjectLibrary = True
        lookupTableName = "$<TARGET_OBJECTS:{}>".format(targetName)

    # Interface libraries are useful for header-only libraries.
    # more info at: http://mariobadr.com/creating-a-header-only-library-with-cmake.html
    if arguments and arguments[0] == 'INTERFACE':
        arguments.pop(0)
        interfaceLibrary = True

    # IMPORTED target node doesn't have any more argument to expand
    # ALIAS target node points to another target node, so the logic behind it is a little different
    if arguments and arguments[0] not in ('IMPORTED', 'ALIAS'):
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
    flattedTargetName = flattenAlgorithmWithConditions(vmodel.expand([targetName]), useCache=False)
    if flattedTargetName:
        for item in flattedTargetName:
            # We already set a key with the name targetNode
            if item[0] != targetName:
                lookupTable.setKey("t:{}".format(item[0]), targetNode)

    if 'IMPORTED' in arguments:
        targetNode.imported = True

    if 'ALIAS' in arguments:
        aliasTarget = lookupTable.getKey('t:{}'.format(arguments[1]))
        nextNode = aliasTarget

    nextNode = util_handleConditions(nextNode, targetName)
    targetNode.sources = nextNode


# Very similar to while command
def forEachCommand(arguments):
    vmodel = VModel.getInstance()

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
