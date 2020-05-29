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


def setCommand(arguments):
    variable_name = "${{{}}}".format(arguments.pop(0))
    if arguments:
        # Retrieve or create node for each argument
        node = vmodel.expand(arguments)
    else:  # SET (VAR) // Removes the definition of VAR.
        lookupTable.deleteKey(variable_name)
        return
    # Each variable has its own RefNode
    variableNode = RefNode(variable_name, node)
    # This function will handle scenarios like if conditions and reassignment before adding node to the graph
    vmodel.addVariableNode(variableNode, "PARENT_SCOPE" in arguments)


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


class CMakeExtractorListener(CMakeListener):
    def enterSetCommand(self, ctx: CMakeParser.SetCommandContext):
        # Extract arguments
        arguments = [child.getText() for child in ctx.argument().getChildren() if not isinstance(child, TerminalNode)]
        if vmodel.shouldRecordCommand():
            forEachCommands.append(('set', arguments))
        else:
            setCommand(arguments)

    def enterIfCommand(self, ctx: CMakeParser.IfCommandContext):
        vmodel.setInsideIf()
        vmodel.ifConditions.append(" ".join([argument.getText() for argument in ctx.ifStatement().argument().children if
                                             not isinstance(argument, TerminalNode)]))

    def enterElseIfStatement(self, ctx: CMakeParser.ElseIfStatementContext):
        vmodel.ifConditions.pop()
        vmodel.ifConditions.append(ctx.argument().getText())

    def enterElseStatement(self, ctx: CMakeParser.ElseStatementContext):
        condition = vmodel.ifConditions.pop(0)
        vmodel.ifConditions.append("ELSE_" + condition)

    def exitIfCommand(self, ctx: CMakeParser.IfCommandContext):
        vmodel.setOutsideIf()
        vmodel.ifConditions.pop()

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

        if commandId == 'unset':
            variable_name = "${{{}}}".format(arguments.pop(0))
            parentScope = False
            if "PARENT_SCOPE" in arguments:
                parentScope = True
            lookupTable.deleteKey(variable_name, parentScope)

        if commandId == 'foreach':
            forEachCommand(arguments)

        if commandId == 'endforeach':
            vmodel.disableRecordCommands()
            for arg in forEachArguments:
                for commandType, commandArgs in forEachCommands:
                    newArgs = [i.replace(forEachVariableName, arg) for i in  commandArgs]
                    if commandType == 'set':
                        setCommand(newArgs)

        if commandId == 'add_subdirectory':
            tempProjectDir = project_dir
            project_dir = os.path.join(project_dir, ctx.argument().single_argument()[0].getText())
            parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
            project_dir = tempProjectDir

        if commandId == 'add_library':
            targetName = arguments.pop(0)
            scope = None
            if arguments[0] in ('STATIC', 'SHARED', 'MODULE'):
                scope = arguments.pop(0)
            nextNode = vmodel.expand(arguments)
            targetNode = TargetNode(targetName, nextNode)
            targetNode.scope = scope
            vmodel.addNode(targetNode)

        if commandId == 'add_executable':
            targetName = arguments.pop(0)
            nextNode = vmodel.expand(arguments)
            targetNode = TargetNode(targetName, nextNode)
            vmodel.addNode(targetNode)

        if commandId == 'list':
            action = arguments.pop(0)
            listName = "${{{}}}".format(arguments.pop(0))
            if action.upper() != 'APPEND':
                raise Exception('NOT_IMPLEMENTED')

            listVModel = vmodel.findNode(listName)
            if listVModel is None:
                listVModel = RefNode(listName, ConcatNode("LIST_" + listName + ",".join(arguments)))
                vmodel.addNode(listVModel)

            concatNode = listVModel.pointTo
            if not isinstance(concatNode, ConcatNode):
                concatNode = ConcatNode("LIST_" + listName)
                concatNode.addNode(listVModel.pointTo)
                listVModel.pointTo = concatNode

            argumentSet = vmodel.flatten(arguments)
            for item in argumentSet:
                node = vmodel.findNode(item)
                if node is None:
                    node = vmodel.expand([item])
                concatNode.addNode(node)

        if commandId == 'target_include_directories':
            pass

        if commandId == 'target_compile_definitions':
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

        if commandId == 'target_link_libraries':
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
