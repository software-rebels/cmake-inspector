from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
from antlr4.tree.Tree import TerminalNode
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from grammar.CMakeListener import CMakeListener

from neomodel import StructuredNode, StringProperty, RelationshipTo, RelationshipFrom, config
import sys
import os
import csv

config.DATABASE_URL = 'bolt://neo4j:123@localhost:7687'

commands_freq = dict()
project_dir = ""


class SourceFile(StructuredNode):
    name = StringProperty()


class Target(StructuredNode):
    TYPES = {'LIBRARY': 'Library', 'EXECUTABLE': 'Executable'}
    type = StringProperty(required=True, choices=TYPES)


class Executable(StructuredNode):
    name = StringProperty(unique_index=True)
    target = StringProperty()
    files = RelationshipTo(SourceFile, 'HAS')


class NodeList():
    pass


class Node():
    pass


class Lookup():
    items = [{}]

    def newScope(self):
        self.items.append({})

    def addKey(self, key, value):
        self.items[-1][key] = value

    def getKey(self, key):
        for table in reversed(self.items):
            if key in table:
                return table.get(key)
            return None

    def dropScope(self):
        self.items.pop()


lookupTable = Lookup()


class CMakeExtractorListener(CMakeListener):
    def enterCommand_invocation(self, ctx: CMakeParser.Command_invocationContext):
        global project_dir
        commandId = ctx.Identifier().getText()
        if commandId not in ('add_subdirectory', 'endif', 'include'):
            if commandId in commands_freq:
                commands_freq[commandId] += 1
            else:
                commands_freq[commandId] = 1

        if commandId == 'add_subdirectory':
            tempProjectDir = project_dir
            project_dir = os.path.join(project_dir, ctx.single_argument()[0].getText())
            parseFile(os.path.join(project_dir, 'CMakeLists.txt'))
            project_dir = tempProjectDir

        if commandId == 'include':
            if os.path.exists(os.path.join(project_dir, ctx.argument().single_argument()[0].getText())):
                parseFile(os.path.join(project_dir, ctx.argument().single_argument()[0].getText()))
        # if ctx.Identifier().getText() == "add_executable":
        #     executable = Executable()
        #     invocationArguments = (child for child in ctx.getChildren() if not isinstance(child, TerminalNode))
        #     for (index, argument) in enumerate(invocationArguments):
        #         if index == 0:
        #             executable.name = argument.getText()
        #             executable.save()
        #             continue

        #         if argument.getText() in ('WIN32', 'MACOSX_BUNDLE', 'EXCLUDE_FROM_ALL'):
        #             executable.target = argument.getText()
        #             executable.save()
        #             continue

        #         sourceFile = SourceFile(name = argument.getText()).save()
        #         executable.files.connect(sourceFile)


def parseFile(filePath):
    inputFile = FileStream(filePath)
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
    with open('commandsfreq.csv', 'w') as csvOut:
        writer = csv.DictWriter(csvOut, fieldnames=['command', 'freq'])
        writer.writeheader()
        for key in commands_freq:
            writer.writerow({
                "command": key,
                "freq": commands_freq[key]
            })


if __name__ == "__main__":
    main(sys.argv)
