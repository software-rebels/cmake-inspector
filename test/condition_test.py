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

    def test_simple_condition(self):
        text = """
        set(var_a 1)
        set(var_b false)
        
        set(foo mehran)
        
        if(var_a OR var_b)
            set(foo bar)
        elseif(a) --> NOT(var_a or var_b) and a
            <>
        elseif(b) --> NOT(NOT(var_a or var_b) and a) and b
            <>
        endif()
        
        if(NOT var_a)
            set(foo doe)
        endif()
        """
        self.runTool(text)
        # self.vmodel.export()
        var = self.lookup.getKey('${foo}')
        a = flattenAlgorithmWithConditions(var)
        print(a)