import logging

from operator import concat
from re import L
from z3.z3 import Concat

from algorithms.algorithms import flattenAlgorithmWithConditions
from condition_data_structure import Rule
from datastructs import Lookup, CustomCommandNode, TargetNode, ConcatNode, \
WhileCommandNode, DefinitionNode, CommandDefinitionNode, DefinitionPair, TargetCompileDefinitionNode, TestNode, ForeachCommandNode
from grammar.CMakeLexer import CMakeLexer, CommonTokenStream, InputStream
from grammar.CMakeParser import CMakeParser
from utils.utils import *


def setCommand(arguments):
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()
    # TODO: @Farshad: Why did you add this line?
    if len(arguments) == 1:
        arguments.append('')
    rawVarName = arguments.pop(0).strip('"')
    variable_name = "${{{}}}".format(rawVarName)
    parentScope = False
    if 'PARENT_SCOPE' in arguments:
        parentScope = True
        arguments.pop(arguments.index('PARENT_SCOPE'))
    # Remove arguments related to cache
    if 'CACHE' in arguments:
        idx = arguments.index('CACHE')
        arguments = arguments[:idx] + arguments[idx+3:]
        if 'FORCE' in arguments:
            arguments.pop(arguments.index('FORCE'))
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


def foreachCommand():
    vmodel = VModel.getInstance()
    # customCommand = CustomCommandNode("WHILE({})".format(util_getStringFromList(arguments)))
    vmodel.pushCurrentLookupTable()
    # We want to show the dependency between while command and newly created nodes. We compare nodes before and after
    # while loop and connect while command node to them.
    vmodel.nodeStack.append(list(vmodel.nodes))


# We compare lookup table before while and after that. For any changed variable, or newly created one,
# the tool will add the RefNode to the while command node, then it creates a new RefNode pointing to the
# While command node
def endForeachCommand(foreachVars):
    instantCommands = ['include']
    shouldRunInstantly = False
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()

    lastPushedLookup = vmodel.getLastPushedLookupTable()

    command = ForeachCommandNode(foreachVars[0], foreachVars[1])
    prevNodeStack = vmodel.nodeStack.pop()
    iterLoop = vmodel.expand([foreachVars[1]])
    loopVar = vmodel.expand([foreachVars[0]]);
    refNodeVars = CustomCommandNode("foreach_vars_{}_{}".format(foreachVars[0], foreachVars[1]))
    refNodeVars.pointTo.append(iterLoop)
    refNodeVars.pointTo.append(loopVar)
    command.pointTo.append((refNodeVars))
    for item in vmodel.nodes:
        if item not in prevNodeStack:
            command.pointTo.append(item)
            if item.rawName in instantCommands:
                shouldRunInstantly = True

    for key in lookupTable.items[-1].keys():
        if key not in lastPushedLookup.items[-1].keys() or lookupTable.getKey(key) != lastPushedLookup.getKey(key):
            # command.pointTo.append(lookupTable.getKey(key))
            refNode = RefNode("{}_{}".format(key, vmodel.getNextCounter()), command)
            lookupTable.setKey(key, refNode)
            vmodel.nodes.append(refNode)

    if shouldRunInstantly:
        print("[error][foreach] There are foreach commands that are neglected at this point")
        # possibleValues = flattenAlgorithmWithConditions(iterLoop)
        # for item in possibleValues:
        #     setCommand([foreachVars[0],item])

def whileCommand(rule: Rule):
    vmodel = VModel.getInstance()
    # customCommand = CustomCommandNode("WHILE({})".format(util_getStringFromList(arguments)))
    vmodel.pushSystemState(rule)
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
    rule = vmodel.popSystemState()
    command = WhileCommandNode(rule)
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
        refNode.pointTo = util_handleConditions(refNode.pointTo, refNode.name)
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


def addCompileTargetDefinitionsCommand(arguments):
    vmodel = VModel.getInstance()
    lookup = Lookup.getInstance()
    
    targetName = arguments.pop(0)
    targetName = flattenAlgorithmWithConditions(vmodel.expand([targetName]))[0][0]
    targetNode = lookup.getKey('t:{}'.format(targetName))
    assert isinstance(targetNode, TargetNode)

    scope = arguments.pop(0)
    to_interface = to_definition = False

    if scope == 'PUBLIC':
        to_interface = to_definition = True
    elif scope == 'PRIVATE':
        to_definition = True
    elif scope == 'INTERFACE':
        to_interface = True
        pass
    else:
        raise ValueError(f'target_compile_definitions is given an invalid scope: {scope}')
    
    definition_names = util_preprocess_definition_names(arguments, force=True)
    
    # Similar to the directory definition case, but since ordering here does not matter
    # we do not have to use DefinitionPair for flipping the path.
    if to_definition:
        new_definition_node = DefinitionNode(from_dir=False)
        new_target_command_node = TargetCompileDefinitionNode()
        next_node = vmodel.expand(definition_names)
        depended_node = util_handleConditions(next_node, next_node.name, None)
        new_target_command_node.commands.append(depended_node)
        new_definition_node.commands.append(new_target_command_node)
        
        current_definition = targetNode.definitions
        if current_definition is not None:
            assert isinstance(current_definition, DefinitionNode)
            new_definition_node.depends.append(targetNode.definitions)
        
        vmodel.nodes.append(new_definition_node)
        targetNode.definitions = new_definition_node

    # Although the code is very similar to above, it has to be separated 
    # because, we do not want interface definition nodes to be dependent 
    # on definition nodes, or vice versa.
    if to_interface:
        new_definition_node = DefinitionNode(from_dir=False)
        new_target_command_node = TargetCompileDefinitionNode()
        next_node = vmodel.expand(definition_names)
        depended_node = util_handleConditions(next_node, next_node.name, None)
        new_target_command_node.commands.append(depended_node)
        new_definition_node.commands.append(new_target_command_node)
        
        current_definition = targetNode.interfaceDefinitions
        if current_definition is not None:
            assert isinstance(current_definition, DefinitionNode)
            new_definition_node.depends.append(targetNode.interfaceDefinitions)

        vmodel.nodes.append(new_definition_node)
        targetNode.interfaceDefinitions = new_definition_node


def handleCompileDefinitionCommand(arguments, command, specific, project_dir):
    # This handles add and remove commands for both preprocessor definitions
    vmodel = VModel.getInstance()
    newDefinitionCommand = CommandDefinitionNode(command=command, specific=specific)
    definitionNode = DefinitionNode(ordering=vmodel.getDefinitionOrder())
    arguments = util_preprocess_definition_names(arguments)
    nextNode = vmodel.expand(arguments)
    targetNode = util_handleConditions(nextNode, nextNode.name, None)
    
    if vmodel.directory_to_properties.get(project_dir) is None:
        vmodel.directory_to_properties[project_dir] = Lookup()
    project_dir_lookup = vmodel.directory_to_properties.get(project_dir)
    
    # To link a new definition node below the last added definition node, thus perserving 
    # the command ordering in the CMAKE file 
    if last_definition_pair := project_dir_lookup.getOwnKey('COMPILE_DEFINITIONS_PAIRS'):
        last_definition_pair.tail.depends.append(definitionNode)
    else: # if we are adding a head node
        last_definition_pair = DefinitionPair(definitionNode)
        vmodel.nodes.append(definitionNode)
        project_dir_lookup.setKey('COMPILE_DEFINITIONS', last_definition_pair.head)

    newDefinitionCommand.commands.append(targetNode)
    newDefinitionCommand.addParent(definitionNode)
    definitionNode.commands.append(newDefinitionCommand)
    last_definition_pair.tail = definitionNode
    project_dir_lookup.setKey('COMPILE_DEFINITIONS_PAIRS', last_definition_pair)


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

# This function handles 
def ECMAddTest(arguments):
    vmodel = VModel.getInstance()
    func_keys = ["link_libraries","test_name","name_prefix","gui"]
    sources = []
    while len(arguments) and arguments[0].lower() not in func_keys:
        sources.append(arguments.pop(0))

    target_name = '.'.join(sources[0].split('.')[:-1])
    libraries = []
    base_name = target_name 
    prefix = ""

    while len(arguments):
        key = arguments.pop(0).lower()
        values = []
        if key == "link_libraries":
            while len(arguments) and arguments[0].lower() not in func_keys:
                values.append(arguments.pop(0))
            libraries = values
        if key == "test_name":      
            arguments.pop(0) 
            target_name = arguments.pop(0)  
        if key == "name_prefix":
            arguments.pop(0)
            prefix = arguments.pop(0)

    base_name = prefix + target_name 


    # add executable
    # add_executable(${_targetname} ${gui_args} ${_sources})
    execArgs = [target_name]
    for source in sources:
        execArgs.append(source)
    addTarget(execArgs)
    # Add target link
    # target_link_libraries(${_targetname} ${ARG_LINK_LIBRARIES})
    target_link_arguments = [target_name]
    for library in libraries:
        target_link_arguments.append(library)

    customCommand = CustomCommandNode('target_link_libraries')
    customCommand.commands.append(vmodel.expand(target_link_arguments))
    finalNode = util_handleConditions(customCommand, customCommand.name, None)
    # Next variable should have the target nodes itself or the name of targets
    targetList = flattenAlgorithmWithConditions(customCommand.commands[0].getChildren()[0])
    for target in targetList:
        targetNode = target[0]
        if not isinstance(targetNode, TargetNode):
            targetNode = vmodel.lookupTable.getKey("t:{}".format(targetNode))
        # Now we should have a TargetNode
        assert isinstance(targetNode, TargetNode)
        assert isinstance(target[1], set)
        targetNode.linkLibrariesConditions[finalNode] = target[1]

    vmodel.nodes.append(
        finalNode
    )

    # Add_test [first signature]
    testName = base_name
    testNode = TestNode(testName)
    testNode.command = vmodel.expand([target_name])
    vmodel.nodes.append(testNode)
    
# This function handles both add_library and add_executable
def addTarget(arguments, isExecutable=True):
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()

    targets = []
    targetName = arguments.pop(0)

    for item in flattenAlgorithmWithConditions(vmodel.expand([targetName])):
        targetName = item[0]
        condition = item[1]
        lookupTableName = 't:{}'.format(targetName)
        nextNode = None
        libraryType = None
        isObjectLibrary = False
        interfaceLibrary = None

        # These values may exist in add_library only. There is a type property in TargetNode that we can set
        if arguments and arguments[0] in ('STATIC', 'SHARED', 'MODULE'):
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
        prevNode = None
        if targetNode is None:
            targetNode = TargetNode(targetName, nextNode)
            targetNode.setCompileOptions(vmodel.DIRECTORY_PROPERTIES.getKey('COMPILE_OPTIONS'))
            targetNode.linkLibraries = vmodel.DIRECTORY_PROPERTIES.getKey('LINK_LIBRARIES')
            targetNode.includeDirectories = vmodel.DIRECTORY_PROPERTIES.getKey('INCLUDE_DIRECTORIES')
            lookupTable.setKey(lookupTableName, targetNode)
            vmodel.nodes.append(targetNode)
        else:
            prevNode = targetNode.sources

        if libraryType:
            targetNode.libraryType = libraryType

        targetNode.isExecutable = isExecutable
        targetNode.isObjectLibrary = isObjectLibrary
        targetNode.interfaceLibrary = interfaceLibrary

        # TODO: We have to decide whether keep the experiment to change it
        # EXPERIMENT: We flatten the target name and add all the possible values to the graph as a potential target
        # flattedTargetName = flattenAlgorithmWithConditions(vmodel.expand([targetName]))
        # if flattedTargetName:
        #     for item in flattedTargetName:
        #         # We already set a key with the name targetNode
        #         if item[0] != targetName:
        #             lookupTable.setKey("t:{}".format(item[0]), targetNode)

        if 'IMPORTED' in arguments:
            targetNode.imported = True

        if 'ALIAS' in arguments:
            aliasTarget = lookupTable.getKey('t:{}'.format(arguments[1]))
            nextNode = aliasTarget

        nextNode = util_handleConditions(nextNode, targetName, prevNode, condition)
        targetNode.sources = nextNode
        targets.append(targetNode)

    return targets


# Very similar to while command
def forEachCommand(arguments):
    vmodel = VModel.getInstance()

    customCommand = CustomCommandNode("foreach")
    foreachVariable = util_create_and_add_refNode_for_variable(arguments.pop(0), vmodel.expand(arguments))
    customCommand.commands.append(foreachVariable)
    rule = Rule()
    rule.command = customCommand
    rule.setType('foreach')
    vmodel.pushSystemState(rule)
    vmodel.pushCurrentLookupTable()
    # We want to show the dependency between foreach command and newly created nodes. We compare nodes before and after
    # foreach loop and connect foreach command node to them.
    vmodel.nodeStack.append(list(vmodel.nodes))


def processCommand(commandId, args):
    pass
    # possibles = globals().copy()
    # possibles.update(locals())
    # method = possibles.get("{}Command".format(commandId))
    # if not method:
    #     raise NotImplementedError("Method %s not implemented" % commandId)
    # method(args)

