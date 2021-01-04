import json
import unittest
from collections import defaultdict

from antlr4 import CommonTokenStream, ParseTreeWalker, InputStream

from analyze import buildRuntimeGraph, printFilesForATarget
from extract import CMakeExtractorListener
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from datastructs import VModel, Lookup, RefNode, ConcatNode, LiteralNode, SelectNode, flattenAlgorithm, \
    CustomCommandNode, getFlattedArguments, TargetNode, TestNode, OptionNode, \
    flattenAlgorithmWithConditions, FinalTarget, Node


class TestConditions(unittest.TestCase):

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

    def test_if_statement_logic_expression(self):
        text = """
        set(foo on)
        if(foo AND ON)
            set(bar off)
        endif(foo)
        """
        self.runTool(text)
        self.vmodel.export()
        # condition = self.vmodel.ru