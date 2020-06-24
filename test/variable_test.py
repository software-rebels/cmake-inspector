import unittest

from antlr4 import CommonTokenStream, ParseTreeWalker, InputStream
from extract import CMakeExtractorListener
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from datastructs import VModel, Lookup, RefNode, ConcatNode, LiteralNode, SelectNode, flattenAlgorithm, \
    CustomCommandNode, getFlattedArguments, TargetNode


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
        self.assertEqual(self.lookup.getVariableHistory("${var}")[3],
                         self.lookup.getKey("${out_var}").pointTo.pointTo[0])

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
        self.assertIsInstance(self.lookup.getKey("t:helloDemo").getPointTo(), ConcatNode)
        self.assertEqual("demo.cxx", self.lookup.getKey("t:helloDemo").getPointTo().getChildren()[0].getValue())

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
        self.assertIsInstance(self.lookup.getKey("t:foo").getPointTo(), SelectNode)
        self.assertIsInstance(self.lookup.getKey("t:foo").getPointTo().trueNode, SelectNode)
        self.assertEqual("john.c", self.lookup.getKey("t:foo").getPointTo().falseNode.getValue())

    def test_add_compile_option(self):
        text = """
            add_compile_options(-Wall -Wextra -pedantic -Werror)
            add_executable(foo bar.c)
        """
        self.runTool(text)
        self.assertEqual(4, len(self.lookup.getKey("t:foo").definitions.getChildren()[0].getChildren()))

    def test_add_compile_option_in_if_statement(self):
        text = """
            add_executable(john doe.c)
            add_compile_options(-Ddebug)
            add_executable(cat dog.c)
            if (1)
                add_compile_options(/W4 /WX)
            else()
                add_compile_options(-Wall -Wextra -pedantic -Werror)
            endif()
            add_executable(foo bar.c)
        """
        self.runTool(text)
        self.assertIsNone(self.lookup.getKey("t:john").definitions)
        self.assertEqual('-Ddebug', self.lookup.getKey("t:cat").definitions.getChildren()[0].getValue())
        self.assertEqual(3, len(self.lookup.getKey("t:foo").definitions.getChildren()))

    def test_file_write_with_variable_in_filename(self):
        text = """
        set(var1 foo.txt)
        file(WRITE ${var1} "Hey John Doe!")
        """
        self.runTool(text)
        self.assertIn(self.lookup.getKey("${var1}"), self.vmodel.findNode('FILE.(WRITE ${var1})_1').getChildren())
        self.assertIn(self.vmodel.findNode('"Hey John Doe!"'),
                      self.vmodel.findNode('FILE.(WRITE ${var1})_1').getChildren())

    def test_file_write_with_variable_in_content_part(self):
        text = """
        set(var2 bar)
        file(APPEND baz.txt "Hey ${var2}")
        """
        self.runTool(text)
        self.assertIn(self.lookup.getKey("${var2}"),
                      self.vmodel.findNode('FILE.(APPEND baz.txt)_1').getChildren()[1].getChildren())
        self.assertEqual("bar", self.lookup.getKey("${var2}").getValue())

    def test_file_read_from_file_into_variable(self):
        text = """
        file(READ foo.txt bar offset 12 limit 20)
        """
        self.runTool(text)
        self.assertEqual(self.vmodel.findNode('FILE.(READ)_0'),
                         self.lookup.getKey('${bar}').getPointTo())

    def test_file_read_from_filename_in_variable(self):
        text = """
        set(john doe.txt)
        file(READ ${john} bar offset 12 limit 20)
        """
        self.runTool(text)
        fileNode = self.vmodel.findNode('FILE.(READ)_1')
        self.assertEqual(fileNode,
                         self.lookup.getKey('${bar}').getPointTo())
        self.assertIn(self.lookup.getKey("${john}"),
                      fileNode.pointTo[0].getChildren())

    def test_file_STRINGS_from_filename_in_variable(self):
        text = """
        set(john doe.txt)
        file(STRINGS ${john} bar offset 12 limit 20)
        """
        self.runTool(text)
        self.assertEqual(self.vmodel.findNode('FILE.(STRINGS)_1'),
                         self.lookup.getKey('${bar}').getPointTo())
        self.assertIn(self.lookup.getKey("${john}"),
                      self.vmodel.findNode('FILE.(STRINGS)_1').pointTo[0].getChildren())

    def test_simple_file_glob(self):
        text = """
        file(GLOB foo /dir/*.cxx)
        """
        self.runTool(text)
        self.assertEqual(self.vmodel.findNode('FILE.(GLOB)_0'), self.lookup.getKey('${foo}').getPointTo())
        self.assertEqual('/dir/*.cxx', self.vmodel.findNode('FILE.(GLOB)_0').getChildren()[0].getValue())

    def test_simple_file_remove(self):
        text = """
        file(REMOVE foo.cxx bar.cxx)
        """
        self.runTool(text)
        self.assertEqual('foo.cxx',
                         self.vmodel.findNode('FILE.(REMOVE)_0').getChildren()[0].getChildren()[0].getValue())
        self.assertEqual('bar.cxx',
                         self.vmodel.findNode('FILE.(REMOVE)_0').getChildren()[0].getChildren()[1].getValue())

    def test_imported_and_alias_add_executable(self):
        text = """
        add_executable(foo IMPORTED)
        add_executable(bar ALIAS foo)
        """
        self.runTool(text)
        self.assertTrue(self.lookup.getKey("t:foo").imported)
        self.assertEqual(self.lookup.getKey("t:foo"), self.lookup.getKey("t:bar").pointTo)

    def test_file_relative_path(self):
        text = """
        set(foo bar)
        file(RELATIVE_PATH john ${foo} sample.cxx)
        """
        self.runTool(text)
        fileNode = self.lookup.getKey("${john}").pointTo
        self.assertIsInstance(fileNode, CustomCommandNode)
        self.assertEqual('bar sample.cxx', " ".join(getFlattedArguments(fileNode.pointTo[0])))

    def test_file_to_path(self):
        text = """
        file(TO_CMAKE_PATH "/bar/test" foo)
        file(TO_NATIVE_PATH "/baz/" john)
        """
        self.runTool(text)
        fileNode1 = self.lookup.getKey("${foo}").pointTo
        fileNode2 = self.lookup.getKey("${john}").pointTo
        self.assertIsInstance(fileNode1, CustomCommandNode)
        self.assertIsInstance(fileNode2, CustomCommandNode)
        self.assertEqual('"/bar/test"', fileNode1.pointTo[0].getValue())

    def test_file_timestamp(self):
        text = """
        file(TIMESTAMP foo.cxx bar someformat UTC)
        """
        self.runTool(text)
        barVariable = self.lookup.getKey("${bar}")
        fileNode = barVariable.pointTo
        self.assertIsInstance(fileNode, CustomCommandNode)
        self.assertEqual("foo.cxx someformat UTC", " ".join(getFlattedArguments(fileNode.pointTo[0])))

    def test_file_generate_output_command(self):
        text = """
        set(foo bar)
        file(GENERATE OUTPUT outfile.txt INPUT infile.txt CONDITION ${foo})
        """
        self.runTool(text)
        fileNode = self.vmodel.findNode('FILE.(GENERATE OUTPUT)_1')
        self.assertEqual("outfile.txt INPUT infile.txt CONDITION bar",
                         " ".join(getFlattedArguments(fileNode.pointTo[0])))

    def test_file_copy_install(self):
        text = """
        file(COPY a.cxx b.cxx DESTINATION /home FILE_PERMISSIONS 644)
        """
        self.runTool(text)
        fileNode = self.vmodel.findNode('FILE.(COPY)_0')
        self.assertEqual('a.cxx b.cxx DESTINATION /home FILE_PERMISSIONS 644',
                         " ".join(getFlattedArguments(fileNode.pointTo[0])))

    def test_find_file_command(self):
        text = """
        find_file(foo bar.txt /home /var)
        """
        self.runTool(text)
        foundVar = self.lookup.getKey("${foo}")
        notFoundVar = self.lookup.getKey("${foo-NOTFOUND}")
        fileNode = self.vmodel.findNode('find_file_0')
        self.assertEqual(fileNode, foundVar.pointTo)
        self.assertEqual(fileNode, notFoundVar.pointTo)
        self.assertEqual('bar.txt /home /var', " ".join(getFlattedArguments(fileNode.pointTo[0])))

    def test_add_library_simple_command(self):
        text = """
        add_library(foo SHARED bar.cxx john.cxx)
        """
        self.runTool(text)
        libraryNode = self.lookup.getKey('t:foo')
        self.assertEqual(False, libraryNode.isExecutable)
        self.assertEqual('SHARED', libraryNode.libraryType)
        self.assertEqual('bar.cxx john.cxx', " ".join(getFlattedArguments(libraryNode.pointTo)))

    def test_add_library_in_if(self):
        text = """
        if(1)
          add_library(foo bar.c)
        elseif(0)
          add_library(foo doe.c)
        else() 
          add_library(foo john.c)
        endif()
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey("t:foo").getPointTo(), SelectNode)
        self.assertIsInstance(self.lookup.getKey("t:foo").getPointTo().trueNode, SelectNode)
        self.assertEqual("john.c", self.lookup.getKey("t:foo").getPointTo().falseNode.getValue())
        self.assertEqual('STATIC', self.lookup.getKey("t:foo").libraryType)

    def test_add_imported_library(self):
        text = """
        add_library(foo MODULE IMPORTED)
        """
        self.runTool(text)
        libraryNode = self.lookup.getKey('t:foo')
        self.assertEqual(False, libraryNode.isExecutable)
        self.assertEqual('MODULE', libraryNode.libraryType)
        self.assertTrue(libraryNode.imported)
        self.assertIsNone(libraryNode.pointTo)

    def test_add_aliased_library(self):
        text = """
        add_library(foo bar.c)
        add_library(john ALIAS foo)
        """
        self.runTool(text)
        fooL = self.lookup.getKey('t:foo')
        johnL = self.lookup.getKey('t:john')
        self.assertEqual(False, johnL.isExecutable)
        self.assertEqual(fooL, johnL.pointTo)

    def test_add_object_library(self):
        text = """
        add_library(foo OBJECT bar.cxx john.cxx)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey('$<TARGET_OBJECTS:foo>')
        self.assertIsNone(self.lookup.getKey('t:foo'))
        self.assertTrue(targetNode.isObjectLibrary)
        self.assertEqual('bar.cxx john.cxx', " ".join(getFlattedArguments(targetNode.pointTo)))

    def test_interface_library(self):
        text = """
        add_library(foo INTERFACE IMPORTED)
        """
        self.runTool(text)
        libraryNode = self.lookup.getKey('t:foo')
        self.assertTrue(libraryNode.interfaceLibrary)
        self.assertTrue(libraryNode.imported)
        self.assertIsNone(libraryNode.pointTo)

    def test_macro_should_change_variable_in_current_scope(self):
        text = """
        set(This foo)
        macro(simple REQUIRED_ARG)
            set(${REQUIRED_ARG} "From SIMPLE")
        endmacro()
        simple(This)
        set(bar ${This})
        """
        self.runTool(text)
        self.assertEqual(self.lookup.getVariableHistory('${This}')[1], self.lookup.getKey('${This}'))
        self.assertEqual(self.lookup.getVariableHistory('${This}')[1], self.lookup.getKey('${bar}').getPointTo())
        self.assertEqual("\"From SIMPLE\"", self.lookup.getKey('${This}').getPointTo().getValue())

    def test_configure_file(self):
        text = """
        set(foo bar)
        set(john doe)
        configure_file ( 
          ${foo}/output.rb.in
          ${john}/output.rb
          ESCAPE_QUOTES
        )
        """
        self.runTool(text)
        functionNode = self.vmodel.findNode("configure_file_2")
        self.assertEqual("bar/output.rb.in doe/output.rb ESCAPE_QUOTES",
                         " ".join(getFlattedArguments(functionNode.pointTo[0])))

    def test_execute_process(self):
        text = """
        set(timeout_var 60)
        execute_process(COMMAND cmd1 args1
                        COMMAND cmd2 args2
                        TIMEOUT ${timeout_var}
                        OUTPUT_VARIABLE out_var
                        ERROR_VARIABLE error_var
                        RESULT_VARIABLE result_var
                        OUTPUT_QUIET
                        )
        """
        self.runTool(text)
        outputVar = self.lookup.getKey('${out_var}')
        errorVar = self.lookup.getKey('${error_var}')
        resultVar = self.lookup.getKey('${result_var}')
        executeNode = self.vmodel.findNode('execute_process_1')
        self.assertEqual(executeNode, outputVar.pointTo)
        self.assertEqual(executeNode, errorVar.pointTo)
        self.assertEqual(executeNode, resultVar.pointTo)
        self.assertEqual("COMMAND cmd1 args1 COMMAND cmd2 args2 TIMEOUT 60 OUTPUT_VARIABLE out_var "
                         "ERROR_VARIABLE error_var RESULT_VARIABLE result_var OUTPUT_QUIET",
                         " ".join(getFlattedArguments(executeNode.pointTo[0])))

    def test_site_name(self):
        text = """
        site_name(foo)
        """
        self.runTool(text)
        fooVar = self.lookup.getKey("${foo}")
        siteVar = self.vmodel.findNode("site_name_0")
        self.assertEqual(siteVar, fooVar.pointTo)
        self.assertEqual("foo", flattenAlgorithm(siteVar.pointTo[0])[0])

    def test_separate_arguments(self):
        text = """
        separate_arguments(foo UNIX_COMMAND "--port=123 --host=127.0.0.1")
        """
        self.runTool(text)
        fooVar = self.lookup.getKey("${foo}")
        commandNode = self.vmodel.findNode("separate_arguments_0")
        self.assertEqual(commandNode, fooVar.pointTo)
        self.assertEqual("UNIX_COMMAND \"--port=123 --host=127.0.0.1\"",
                         " ".join(getFlattedArguments(commandNode.pointTo[0])))

    def test_cmake_minimum_required(self):
        text = """
        cmake_minimum_required(VERSION 3.2)
        """
        self.runTool(text)
        self.assertEqual("3.2", self.vmodel.cmakeVersion)

    def test_add_custom_target_with_dependency(self):
        text = """
        add_executable(foo bar.cxx)
        add_custom_target(john COMMAND joe DEPENDS foo SOURCES baz.cxx)
        """
        self.runTool(text)
        self.vmodel.export()
        self.assertIsInstance(self.lookup.getKey("t:john"), TargetNode)
        self.assertIn(self.lookup.getKey("t:foo"), self.lookup.getKey("t:john").pointTo.listOfNodes)

    def test_add_custom_target_without_dependency(self):
        text = """
        add_custom_target(john COMMAND joe SOURCES baz.cxx)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey("t:john")
        self.assertEqual("COMMAND joe SOURCES baz.cxx", " ".join(getFlattedArguments(targetNode.pointTo)))

    def test_math_function(self):
        text = """
        math(EXPR value "100 * 0xA")
        """
        self.runTool(text)
        val = self.lookup.getKey("${value}")
        mathNode = self.vmodel.findNode('MATH_0')
        self.assertEqual(mathNode, val.pointTo)
        self.assertEqual('"100 * 0xA"', mathNode.pointTo[0].getValue())





if __name__ == '__main__':
    unittest.main()
