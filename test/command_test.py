import json
import unittest
from collections import defaultdict

from antlr4 import CommonTokenStream, ParseTreeWalker, InputStream

from analyze import printFilesForATarget
from extract import CMakeExtractorListener
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from datastructs import Lookup, RefNode, ConcatNode, LiteralNode, SelectNode, \
    CustomCommandNode, TargetNode, TestNode, OptionNode, Node
from algorithms import flattenAlgorithm, flattenAlgorithmWithConditions, getFlattedArguments, flattenCustomCommandNode
from vmodel import VModel


class TestNewCommands(unittest.TestCase):

    def runTool(self, text):
        lexer = CMakeLexer(InputStream(text))
        stream = CommonTokenStream(lexer)
        parser = CMakeParser(stream)
        tree = parser.cmakefile()
        extractor = CMakeExtractorListener()
        walker = ParseTreeWalker()
        walker.walk(extractor, tree)

    def setUp(self) -> None:
        self.vmodel = VModel.getInstance()
        self.lookup = Lookup.getInstance()

    def tearDown(self) -> None:
        VModel.clearInstance()
        Lookup.clearInstance()

    def test_install():
         text = """
        find_path (Magick++_LIBRARY Magick++ /files)
        """
        self.runTool(text)
        foundVar = self.lookup.getKey('${Magick++_LIBRARY}')
        notFoundVar = self.lookup.getKey('${Magick++_LIBRARY-NOTFOUND}')
        commandNode = foundVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(commandNode, notFoundVar.getPointTo())
        self.assertEqual("Magick++ /files",
                         " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_find_program_without_condition(self):
        text = """
        install(TARGETS KPublicTransport EXPORT KPublicTransportTargets ${INSTALL_TARGETS_DEFAULT_ARGS})
        """
        self.runTool(text)
        # foundVar = self.lookup.getKey('${Magick++_LIBRARY}')
        # notFoundVar = self.lookup.getKey('${Magick++_LIBRARY-NOTFOUND}')
        # commandNode = foundVar.getPointTo()
        # self.assertIsInstance(commandNode, CustomCommandNode)
        # self.assertEqual(commandNode, notFoundVar.getPointTo())
        # self.assertEqual("Magick++ /files",
        #                  " ".join(getFlattedArg


if __name__ == '__main__':
    unittest.main()
