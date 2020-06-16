import unittest

from antlr4 import CommonTokenStream, ParseTreeWalker, InputStream
from extract import CMakeExtractorListener
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from datastructs import VModel, Lookup, RefNode, ConcatNode, LiteralNode, SelectNode, flattenAlgorithm, \
    CustomCommandNode


class TestVariableDefinitions(unittest.TestCase):

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

    def test_simple_variable_definition(self):
        text = """
            set(var expression)
        """
        self.runTool(text)
        self.assertEqual(self.lookup.getKey("${var}").getValue(), "expression")

    def test_variable_double_assignment(self):
        text = """
        set(var expression)
        set(var exp2)
        """
        self.runTool(text)
        varHistory = self.lookup.getVariableHistory("${var}")
        self.assertEqual(2, len(varHistory))
        self.assertEqual("exp2", self.lookup.getKey("${var}").getValue())

    def test_variable_convert_to_list(self):
        text = """
        set(var expression)
        list(APPEND var exp2 exp3)
        """
        self.runTool(text)
        varHistory = self.lookup.getVariableHistory("${var}")
        self.assertEqual(2, len(varHistory))
        self.assertIsInstance(varHistory[0].getPointTo(), LiteralNode)
        self.assertIsInstance(varHistory[1].getPointTo(), ConcatNode)
        self.assertEqual(3, len(self.lookup.getKey("${var}").getPointTo().getChildren()))
        self.assertEqual(varHistory[0], self.lookup.getKey("${var}").getPointTo().getChildren()[0])
        self.assertEqual("exp2", self.lookup.getKey("${var}").getPointTo().getChildren()[1].getValue())

    def test_define_list(self):
        text = """
        set(var foo bar)
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey("${var}").getPointTo(), ConcatNode)
        self.assertEqual(2, len(self.lookup.getKey("${var}").getPointTo().getChildren()))

    def test_append_to_list(self):
        text = """
        set(var foo bar)
        list(APPEND var john doe)
        """
        self.runTool(text)
        self.assertEqual(2, len(self.lookup.getVariableHistory("${var}")))
        self.assertEqual(3, len(self.lookup.getKey("${var}").getPointTo().getChildren()))
        self.assertEqual(self.lookup.getVariableHistory("${var}")[0],
                         self.lookup.getKey("${var}").getPointTo().getChildren()[0])

    def test_variable_assignment_inside_simple_if_condition(self):
        text = """
        set(var foo)
        if(1)
          set(var bar)
        endif(1)
        """
        self.runTool(text)
        self.assertEqual(2, len(self.lookup.getVariableHistory("${var}")))
        self.assertIsInstance(self.lookup.getKey("${var}").getPointTo(), SelectNode)
        self.assertEqual("bar", self.lookup.getKey("${var}").getPointTo().trueNode.getValue())
        self.assertEqual("foo", self.lookup.getKey("${var}").getPointTo().falseNode.getValue())

    def test_variable_assign_and_change_inside_if(self):
        text = """
                set(var foo)
                if(1)
                  set(var bar)
                  set(var john)
                endif(1)
                """
        self.runTool(text)
        self.assertEqual(3, len(self.lookup.getVariableHistory("${var}")))
        self.assertIsInstance(self.lookup.getKey("${var}").getPointTo(), SelectNode)
        self.assertEqual("john", self.lookup.getKey("${var}").getPointTo().trueNode.getValue())
        self.assertEqual("foo", self.lookup.getKey("${var}").getPointTo().falseNode.getValue())

    def test_variable_assignment_after_if(self):
        text = """
        set(var foo)
        if(1)
          set(var bar)
        endif(1)
        set(var john)
        """
        self.runTool(text)
        self.assertEqual(3, len(self.lookup.getVariableHistory("${var}")))
        self.assertEqual("john", self.lookup.getKey("${var}").getPointTo().getValue())

    def test_list_assignment_inside_simple_if(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        endif(1)
        """
        self.runTool(text)
        self.assertEqual(2, len(self.lookup.getVariableHistory("${var}")))
        self.assertIsInstance(self.lookup.getKey("${var}").getPointTo(), SelectNode)
        self.assertIsInstance(self.lookup.getKey("${var}").getPointTo().trueNode, ConcatNode)
        self.assertEqual("foo", self.lookup.getKey("${var}").getPointTo().falseNode.getValue())

    def test_list_assignment_in_else_statement(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        else(1)
          list(APPEND var bar baz)
        endif(1)
        """
        self.runTool(text)
        self.assertEqual(self.lookup.getVariableHistory("${var}")[1],
                         self.lookup.getKey("${var}").getPointTo().trueNode)
        self.assertEqual('bar',
                         self.lookup.getKey("${var}").getPointTo().falseNode.listOfNodes[1].getValue())

    def test_list_assignment_in_elseif_and_else_statement(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
        else(1)
          list(APPEND var bar baz)
        endif(1)
        """
        self.runTool(text)
        self.assertEqual(self.lookup.getVariableHistory("${var}")[2],
                         self.lookup.getKey("${var}").getPointTo().trueNode)
        self.assertEqual('bar',
                         self.lookup.getKey("${var}").getPointTo().falseNode.listOfNodes[1].getValue())

    def test_variable_assignment_in_else_statement(self):
        text = """
        set(var foo)
        if(0)
          set(var bar)
        else(0)
          set(var john)
        endif(0)
        """
        self.runTool(text)
        self.assertEqual(3, len(self.lookup.getVariableHistory("${var}")))
        self.assertEqual("john", self.lookup.getKey("${var}").getPointTo().falseNode.getValue())

    def test_variable_in_else_if_statement(self):
        text = """
        set(var foo)
        if(0)
          set(var bar)
        elseif(1)
          set(var john)
        endif(0)
        """
        self.runTool(text)
        self.assertEqual(3, len(self.lookup.getVariableHistory("${var}")))
        self.assertEqual("john", self.lookup.getKey("${var}").getPointTo().trueNode.getValue())
        self.assertEqual(self.lookup.getVariableHistory("${var}")[1],
                         self.lookup.getKey("${var}").getPointTo().falseNode)
        self.assertEqual('(( NOT ( 0 ) ) AND ( 1 ) )', self.lookup.getKey("${var}").getPointTo().condition)

    def test_variable_in_if_else_if_and_else_statements(self):
        text = """
        set(var foo)
        if(0)
          set(var bar)
        elseif(1)
          set(var john)
        else(0)
          set(var doe)
        endif(0)
        """
        self.runTool(text)
        self.assertEqual(4, len(self.lookup.getVariableHistory("${var}")))
        self.assertEqual("doe", self.lookup.getKey("${var}").getPointTo().falseNode.getValue())
        self.assertEqual(self.lookup.getVariableHistory("${var}")[2],
                         self.lookup.getKey("${var}").getPointTo().trueNode)
        self.assertEqual('(( NOT ( 0 ) ) AND ( 1 ) ) OR ( 0 )', self.lookup.getKey("${var}").getPointTo().condition)

    def test_list_length_on_if_statements(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
        else(1)
          list(APPEND var bar baz)
        endif(1)
        list(LENGTH var out_var)
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey("${out_var}").pointTo, CustomCommandNode)
        self.assertEqual(self.lookup.getKey("${var}"), self.lookup.getKey("${out_var}").pointTo.pointTo[0])

    def test_list_sort_on_if_statements(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
        else(1)
          list(APPEND var bar baz)
        endif(1)
        list(SORT var)
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey("${var}").pointTo, CustomCommandNode)
        self.assertEqual(self.lookup.getVariableHistory("${var}")[3], self.lookup.getKey("${var}").pointTo.pointTo[0])

    def test_list_remove_on_if_statements(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
        else(1)
          list(APPEND var bar baz)
        endif(1)
        list(REMOVE_AT var 1 2 3 4)
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey("${var}").pointTo, CustomCommandNode)
        self.assertEqual(self.lookup.getVariableHistory("${var}")[3], self.lookup.getKey("${var}").pointTo.pointTo[0])

    def test_list_find_on_if_statements(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
        else(1)
          list(APPEND var bar baz)
        endif(1)
        list(FIND var foo out_var)
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey("${out_var}").pointTo, CustomCommandNode)
        self.assertEqual(self.lookup.getVariableHistory("${var}")[3], self.lookup.getKey("${out_var}").pointTo.pointTo[0])

    def test_list_multiple_commands_on_if_statements(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
        else(1)
          list(APPEND var bar baz)
        endif(1)
        list(GET var 1 2 3 out_var)
        list(FIND var foo out_var2)
        list(REVERSE var)
        list(FIND var foo out_var3)
        """
        self.runTool(text)
        self.assertEqual(self.lookup.getVariableHistory("${var}")[3],
                         self.lookup.getKey("${out_var}").pointTo.pointTo[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[3],
                         self.lookup.getKey("${out_var2}").pointTo.pointTo[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[4],
                         self.lookup.getKey("${out_var3}").pointTo.pointTo[0])

    def test_list_action_inside_if(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
          list(REVERSE var)
        else(1)
          list(GET var 1 2 3 out_var)
          list(APPEND var bar baz)
        endif(1)
        
        """
        self.runTool(text)

        self.assertIsNone(self.lookup.getKey("${out_var}").pointTo.trueNode)
        self.assertIsInstance(self.lookup.getKey("${out_var}").pointTo.falseNode, CustomCommandNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[3],
                         self.lookup.getKey("${out_var}").pointTo.falseNode.pointTo[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[1],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.falseNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[2],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.trueNode.pointTo[0])

    def test_list_action_2_inside_if(self):
        text = """
        set(var foo)
        if(1)
          list(APPEND var john doe)
        elseif(0)
          list(APPEND var 1 2)
          list(REVERSE var)
        else(1)
          list(APPEND var bar baz)
          list(GET var 1 2 3 out_var)
        endif(1)

        """
        self.runTool(text)
        self.assertIsNone(self.lookup.getKey("${out_var}").pointTo.trueNode)
        self.assertIsInstance(self.lookup.getKey("${out_var}").pointTo.falseNode, CustomCommandNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[4],
                         self.lookup.getKey("${out_var}").pointTo.falseNode.pointTo[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[1],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.falseNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[2],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.trueNode.pointTo[0])

    def test_simple_while_loop(self):
        text = """
        set(a foo)
        set(condition TRUE)
        while(condition)
          set(a ${a}bar)
          set(b mehran${a})
        endwhile()
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey('${a}').pointTo, CustomCommandNode)
        self.assertIsInstance(self.lookup.getKey('${b}').pointTo, CustomCommandNode)
        customCommand = self.lookup.getKey('${b}').pointTo
        self.assertIn(self.lookup.getVariableHistory('${a}')[1], customCommand.pointTo)
        self.assertIn(self.lookup.getVariableHistory('${b}')[0], customCommand.pointTo)

    def test_variable_scoping_function_without_parent_scope(self):
        text = """
        set(This foo)
        function(simple REQUIRED_ARG)
            set(${REQUIRED_ARG} "From SIMPLE")
        endfunction()
        simple(This)
        set(bar ${This})
        """
        self.runTool(text)
        self.assertEqual(self.lookup.getVariableHistory('${This}')[0], self.lookup.getKey('${This}'))
        self.assertEqual(self.lookup.getVariableHistory('${This}')[0], self.lookup.getKey('${bar}').getPointTo())
        self.assertEqual("\"From SIMPLE\"", self.lookup.getVariableHistory('${This}')[1].getPointTo().getValue())

    def test_variable_scoping_function_with_parent_scope(self):
        text = """
        set(This foo)
        function(simple REQUIRED_ARG)
            set(${REQUIRED_ARG} "From SIMPLE" PARENT_SCOPE)
        endfunction()
        simple(This)
        set(bar ${This})
        """
        self.runTool(text)
        self.assertEqual(self.lookup.getKey('${This}'), self.lookup.getKey('${bar}').getPointTo())
        self.assertEqual("\"From SIMPLE\"", self.lookup.getKey('${This}').getPointTo().getValue())

    def test_simple_add_executable(self):
        text = """
        add_executable (helloDemo demo.cxx demo_b.cxx)
        """
        self.runTool(text)
        self.vmodel.export()

    def test_add_executable_in_if(self):
        text = """
        if(1)
          add_executable(foo bar.c)
        elseif(0)
          add_executable(foo doe.c)
        else() 
          add_executable(foo john.c)
        endif()
        """
        self.runTool(text)
        self.vmodel.export()

if __name__ == '__main__':
    unittest.main()
