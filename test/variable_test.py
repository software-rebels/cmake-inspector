import json
import unittest
from collections import defaultdict

from antlr4 import CommonTokenStream, ParseTreeWalker, InputStream

from analyze import printDefinitionsForATarget, printFilesForATarget
from extract import CMakeExtractorListener, getFlattenedDefintionsForTarget, linkDirectory
from grammar.CMakeLexer import CMakeLexer
from grammar.CMakeParser import CMakeParser
from datastructs import CommandDefinitionNode, DefinitionNode, Lookup, RefNode, ConcatNode, LiteralNode, SelectNode, \
    CustomCommandNode, TargetNode, TestNode, OptionNode, Node, Directory
from algorithms import flattenAlgorithm, flattenAlgorithmWithConditions, getFlattedArguments, flattenCustomCommandNode, \
    CycleDetectedException, getFlattenedDefinitionsFromNode, postprocessZ3Output
from vmodel import VModel
from extract import initialize


class TestVariableDefinitions(unittest.TestCase):

    def runTool(self, text):
        initialize(text,False)
        linkDirectory()


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

    def test_list_assignment_with_symbolic_node(self):
        text = """
        set(LIBFOO_TAR_HEADERS
          "${CMAKE_CURRENT_BINARY_DIR}/include/foo/foo.h"
          "${CMAKE_CURRENT_BINARY_DIR}/include/foo/foo_utils.h"
        )
        """
        self.runTool(text)
        self.assertIsNone(self.lookup.getKey("${CMAKE_CURRENT_BINARY_DIR}").pointTo)

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
                         self.lookup.getKey("${var}").getPointTo().falseNode)
        self.assertEqual('bar',
                         self.lookup.getKey("${var}").getPointTo().trueNode.listOfNodes[1].getValue())

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
                         self.lookup.getKey("${var}").getPointTo().falseNode)
        self.assertEqual('bar',
                         self.lookup.getKey("${var}").getPointTo().trueNode.listOfNodes[1].getValue())

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
        self.assertEqual("john", self.lookup.getKey("${var}").getPointTo().trueNode.getValue())

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
        self.assertEqual('((NOT 0) AND 1)', self.lookup.getKey("${var}").getPointTo().getCondition().getText(True))

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
        self.assertEqual("doe", self.lookup.getKey("${var}").getPointTo().trueNode.getValue())
        self.assertEqual(self.lookup.getVariableHistory("${var}")[2],
                         self.lookup.getKey("${var}").getPointTo().falseNode)

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
        self.assertEqual(self.lookup.getKey("${var}"), self.lookup.getKey("${out_var}").pointTo.depends[0])

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
        self.assertEqual(self.lookup.getVariableHistory("${var}")[3], self.lookup.getKey("${var}").pointTo.depends[0])

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
        self.assertEqual(self.lookup.getVariableHistory("${var}")[3], self.lookup.getKey("${var}").pointTo.depends[0])

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
                         self.lookup.getKey("${out_var}").pointTo.depends[0])

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
                         self.lookup.getKey("${out_var}").pointTo.depends[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[3],
                         self.lookup.getKey("${out_var2}").pointTo.depends[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[4],
                         self.lookup.getKey("${out_var3}").pointTo.depends[0])

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

        self.assertIsNone(self.lookup.getKey("${out_var}").pointTo.falseNode)
        self.assertIsInstance(self.lookup.getKey("${out_var}").pointTo.trueNode, CustomCommandNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[3],
                         self.lookup.getKey("${out_var}").pointTo.trueNode.depends[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[1],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.falseNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[2],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.trueNode.depends[0])

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
        self.assertIsNone(self.lookup.getKey("${out_var}").pointTo.falseNode)
        self.assertIsInstance(self.lookup.getKey("${out_var}").pointTo.trueNode, CustomCommandNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[4],
                         self.lookup.getKey("${out_var}").pointTo.trueNode.depends[0])

        self.assertEqual(self.lookup.getVariableHistory("${var}")[1],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.falseNode)

        self.assertEqual(self.lookup.getVariableHistory("${var}")[2],
                         self.lookup.getVariableHistory("${var}")[3].pointTo.trueNode.depends[0])

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
        self.assertEqual("From SIMPLE", self.lookup.getVariableHistory('${This}')[1].getPointTo().getValue())

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
        self.assertEqual("From SIMPLE", self.lookup.getKey('${This}').getPointTo().getValue())

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
        self.assertIsInstance(self.lookup.getKey("t:foo").getPointTo().falseNode, SelectNode)
        self.assertEqual("john.c", self.lookup.getKey("t:foo").getPointTo().trueNode.getChildren()[0].getValue())

    def test_add_compile_option(self):
        text = """
            add_compile_options(-Wall -Wextra -pedantic -Werror)
            add_executable(foo bar.c)
        """
        self.runTool(text)
        # self.vmodel.export()
        self.assertEqual(4, len(self.lookup.getKey("t:foo").compileOptions.getChildren()[0].getChildren()))

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
        self.assertIsNone(self.lookup.getKey("t:john").compileOptions)
        self.assertEqual('-Ddebug', self.lookup.getKey("t:cat").compileOptions.getChildren()[0].getValue())
        self.assertEqual(3, len(self.lookup.getKey("t:foo").compileOptions.getChildren()))

    def test_file_write_with_variable_in_filename(self):
        text = """
        set(var1 foo.txt)
        file(WRITE ${var1} "Hey John Doe!")
        """
        self.runTool(text)
        self.assertIn(self.lookup.getKey("${var1}"), self.vmodel.findNode('FILE.(WRITE ${var1})').getChildren())
        self.assertIn(self.vmodel.findNode('Hey John Doe!'),
                      self.vmodel.findNode('FILE.(WRITE ${var1})').getChildren())

    def test_file_write_with_variable_in_content_part(self):
        text = """
        set(var2 bar)
        file(APPEND baz.txt "Hey ${var2}")
        """
        self.runTool(text)
        self.assertIn(self.lookup.getKey("${var2}"),
                      self.vmodel.findNode('FILE.(APPEND baz.txt)').getChildren()[1].getChildren())
        self.assertEqual("bar", self.lookup.getKey("${var2}").getValue())

    def test_file_read_from_file_into_variable(self):
        text = """
        file(READ foo.txt bar offset 12 limit 20)
        """
        self.runTool(text)
        self.assertEqual(self.vmodel.findNode('FILE.(READ)'),
                         self.lookup.getKey('${bar}').getPointTo())

    def test_file_read_from_filename_in_variable(self):
        text = """
        set(john doe.txt)
        file(READ ${john} bar offset 12 limit 20)
        """
        self.runTool(text)
        fileNode = self.vmodel.findNode('FILE.(READ)')
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
        self.assertEqual(self.vmodel.findNode('FILE.(STRINGS)'),
                         self.lookup.getKey('${bar}').getPointTo())
        self.assertIn(self.lookup.getKey("${john}"),
                      self.vmodel.findNode('FILE.(STRINGS)').pointTo[0].getChildren())

    def test_simple_file_glob(self):
        text = """
        file(GLOB foo files_for_test/*.cxx)
        """
        self.runTool(text)
        fooVar = self.lookup.getKey("${foo}")
        fileCommand = fooVar.getPointTo()
        self.assertIsInstance(fileCommand, CustomCommandNode)
        self.assertEqual(self.vmodel.findNode('FILE'), fileCommand)
        self.assertEqual("GLOB files_for_test/*.cxx", " ".join(getFlattedArguments(fileCommand.commands[0])))
        self.assertEqual(['./files_for_test/a.cxx', './files_for_test/b.cxx', './files_for_test/c.cxx'],
                         sorted([item[0] for item in flattenCustomCommandNode(fileCommand, {}, [])]))

    def test_simple_file_remove(self):
        text = """
        file(REMOVE foo.cxx bar.cxx)
        """
        self.runTool(text)
        self.assertEqual('foo.cxx',
                         self.vmodel.findNode('FILE.(REMOVE)').getChildren()[0].getChildren()[0].getValue())
        self.assertEqual('bar.cxx',
                         self.vmodel.findNode('FILE.(REMOVE)').getChildren()[0].getChildren()[1].getValue())

    def test_imported_and_alias_add_executable(self):
        text = """
        add_executable(foo IMPORTED)
        add_executable(bar ALIAS foo)
        """
        self.runTool(text)
        self.assertTrue(self.lookup.getKey("t:foo").imported)
        self.assertEqual(self.lookup.getKey("t:foo"), self.lookup.getKey("t:bar").getPointTo())

    def test_file_relative_path(self):
        text = """
        set(foo bar)
        file(RELATIVE_PATH john ${foo} sample.cxx)
        """
        self.runTool(text)
        fileNode = self.lookup.getKey("${john}").pointTo
        self.assertIsInstance(fileNode, CustomCommandNode)
        self.assertEqual('RELATIVE_PATH bar sample.cxx', " ".join(getFlattedArguments(fileNode.pointTo[0])))

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
        self.assertEqual('/bar/test', fileNode1.pointTo[0].getValue())

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
        fileNode = self.vmodel.findNode('FILE.(GENERATE OUTPUT)')
        self.assertEqual("outfile.txt INPUT infile.txt CONDITION bar",
                         " ".join(getFlattedArguments(fileNode.pointTo[0])))

    def test_file_copy_install(self):
        text = """
        file(COPY a.cxx b.cxx DESTINATION /home FILE_PERMISSIONS 644)
        """
        self.runTool(text)
        fileNode = self.vmodel.findNode('FILE.(COPY)')
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
        self.assertEqual('bar.cxx john.cxx', " ".join(getFlattedArguments(libraryNode.getPointTo())))

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
        self.assertIsInstance(self.lookup.getKey("t:foo").getPointTo().falseNode, SelectNode)
        self.assertEqual("john.c", self.lookup.getKey("t:foo").getPointTo().trueNode.getChildren()[0].getValue())
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
        self.assertIsNone(libraryNode.getPointTo())

    def test_add_aliased_library(self):
        text = """
        add_library(foo bar.c)
        add_library(john ALIAS foo)
        """
        self.runTool(text)
        fooL = self.lookup.getKey('t:foo')
        johnL = self.lookup.getKey('t:john')
        self.assertEqual(False, johnL.isExecutable)
        self.assertEqual(fooL, johnL.getPointTo())

    def test_add_object_library(self):
        text = """
        add_library(foo OBJECT bar.cxx john.cxx)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey('$<TARGET_OBJECTS:foo>')
        self.assertIsNone(self.lookup.getKey('t:foo'))
        self.assertTrue(targetNode.isObjectLibrary)
        self.assertEqual('bar.cxx john.cxx', " ".join(getFlattedArguments(targetNode.getPointTo())))

    def test_interface_library(self):
        text = """
        add_library(foo INTERFACE IMPORTED)
        """
        self.runTool(text)
        libraryNode = self.lookup.getKey('t:foo')
        self.assertTrue(libraryNode.interfaceLibrary)
        self.assertTrue(libraryNode.imported)
        self.assertIsNone(libraryNode.getPointTo())

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
        self.assertEqual("From SIMPLE", self.lookup.getKey('${This}').getPointTo().getValue())

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
        functionNode = self.vmodel.findNode("configure_file")
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
        executeNode = self.vmodel.findNode('execute_process')
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
        self.assertEqual("UNIX_COMMAND --port=123 --host=127.0.0.1",
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
        self.assertIsInstance(self.lookup.getKey("t:john"), TargetNode)
        self.assertIn(self.lookup.getKey("t:foo"), self.lookup.getKey("t:john").getPointTo().listOfNodes)

    def test_add_custom_target_without_dependency(self):
        text = """
        add_custom_target(john COMMAND joe SOURCES baz.cxx)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey("t:john")
        self.assertEqual("COMMAND joe SOURCES baz.cxx", " ".join(getFlattedArguments(targetNode.getPointTo())))

    def test_math_function(self):
        text = """
        math(EXPR value "100 * 0xA")
        """
        self.runTool(text)
        val = self.lookup.getKey("${value}")
        mathNode = self.vmodel.findNode('MATH_0')
        self.assertEqual(mathNode, val.pointTo)
        self.assertEqual('100 * 0xA', mathNode.pointTo[0].getValue())

    def test_set_directory_properties_without_condition(self):
        text = """
        set_directory_properties(PROPERTIES INCLUDE_DIRECTORIES foo LINK_DIRECTORIES bar)
        """
        self.runTool(text)
        self.assertIsInstance(self.vmodel.DIRECTORY_PROPERTIES.getKey('INCLUDE_DIRECTORIES'), ConcatNode)
        self.assertEqual('foo',
                         flattenAlgorithm(self.vmodel.DIRECTORY_PROPERTIES.getKey('INCLUDE_DIRECTORIES'))[0])
        self.assertEqual('bar',
                         flattenAlgorithm(self.vmodel.DIRECTORY_PROPERTIES.getKey('LINK_DIRECTORIES'))[0])

    def test_get_directory_property_without_condition_without_new_directory(self):
        text = """
        set_directory_properties(PROPERTIES INCLUDE_DIRECTORIES foo LINK_DIRECTORIES bar)
        get_directory_property(john INCLUDE_DIRECTORIES)
        get_directory_property(doe DIRECTORY . LINK_DIRECTORIES)
        get_directory_property(baz SOMETHING)
        """
        self.runTool(text)
        # self.vmodel.export()
        johnVar = self.lookup.getKey("${john}")
        doeVar = self.lookup.getKey("${doe}")
        bazVar = self.lookup.getKey("${baz}")
        self.assertEqual('foo',
                         flattenAlgorithm(johnVar.getPointTo())[0])
        self.assertEqual('bar',
                         flattenAlgorithm(doeVar.getPointTo())[0])
        self.assertIsNone(bazVar.pointTo)

    def test_get_directory_property_without_condition_without_new_directory_for_variable(self):
        text = """
        set(foo bar)
        get_directory_property(john DEFINITION foo)
        get_directory_property(doe DIRECTORY . DEFINITION foo)
        get_directory_property(baz DEFINITION SOMETHING)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        doeVar = self.lookup.getKey("${doe}")
        bazVar = self.lookup.getKey("${baz}")
        self.assertEqual(self.lookup.getKey('${foo}'), johnVar.pointTo)
        self.assertEqual(self.lookup.getKey('${foo}'), doeVar.pointTo)
        self.assertIsNone(bazVar.pointTo)

    def test_get_cmake_property_variables_very_simple_usage(self):
        text = """
        set(foo bar)
        set(john doe)
        get_cmake_property(baz VARIABLES)
        """
        self.runTool(text)
        self.assertEqual("CMAKE_CURRENT_SOURCE_DIR CMAKE_SOURCE_DIR CMAKE_CURRENT_LIST_DIR foo john", " ".join(getFlattedArguments(self.lookup.getKey("${baz}").pointTo)))

    def test_add_custom_command_super_simple(self):
        text = """
        add_custom_command(
            OUTPUT foo
            COMMAND touch bar
            COMMAND john doe
        )
        """
        self.runTool(text)
        foo = self.vmodel.findNode('foo')
        self.assertIsInstance(foo.pointTo, CustomCommandNode)
        customCommand = foo.pointTo
        self.assertEqual(2, len(customCommand.commands))
        self.assertEqual('touch bar', " ".join(getFlattedArguments(customCommand.commands[0])))

    def test_add_custom_command_with_main_dependency(self):
        text = """
        add_executable(exec file.cxx)
        add_custom_command(
            OUTPUT foo
            COMMAND touch bar
            MAIN_DEPENDENCY exec
        )
        """
        self.runTool(text)
        foo = self.vmodel.findNode('foo')
        customCommand = foo.pointTo
        self.assertEqual(self.lookup.getKey('t:exec'), customCommand.depends[0])

    def test_add_custom_command_with_main_dependency_and_depends(self):
        text = """
        add_executable(exec file.cxx)
        add_library(libb file2.cxx)
        add_custom_command(
            OUTPUT foo
            COMMAND touch bar
            MAIN_DEPENDENCY exec
            DEPENDS libb
        )
        """
        self.runTool(text)
        foo = self.vmodel.findNode('foo')
        customCommand = foo.pointTo
        self.assertIsInstance(customCommand.depends[0], ConcatNode)

    def test_add_custom_command_simple_with_variable(self):
        text = """
        set(LIBFOO_TAR_HEADERS
          "${CMAKE_CURRENT_BINARY_DIR}/include/foo/foo.h"
          "${CMAKE_CURRENT_BINARY_DIR}/include/foo/foo_utils.h"
        )
        
        add_custom_command(OUTPUT ${LIBFOO_TAR_HEADERS}
          COMMAND make -E tar xzf "${CMAKE_CURRENT_SOURCE_DIR}/libfoo/foo.tar"
          COMMAND make -E touch ${LIBFOO_TAR_HEADERS}
          WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/include/foo"
          DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/libfoo/foo.tar"
          COMMENT "Unpacking foo.tar"
          VERBATIM
        )
        """
        self.runTool(text)
        # TODO: We have problem in this sample

    def test_add_custom_command_for_target_pre_build(self):
        text = """
        add_executable(foo bar.cxx)
        add_custom_command(TARGET foo PRE_BUILD
                           COMMAND cmd1)
        """
        self.runTool(text)
        lib = self.lookup.getKey("t:foo")
        self.assertIsInstance(lib.linkLibraries.getChildren()[0], CustomCommandNode)

    def test_add_custom_command_for_target_post_build(self):
        text = """
        add_executable(foo bar.cxx)
        add_custom_command(TARGET foo POST_BUILD
                           COMMAND cmd1)
        """
        self.runTool(text)
        command = self.vmodel.findNode('custom_command')
        lib = self.lookup.getKey('t:foo')
        self.assertEqual(lib, command.depends[0])

    def test_build_command_with_variable(self):
        text = """
        build_command(foo
              CONFIGURATION bar_config
              TARGET john_target
              PROJECT_NAME doe_project
             )
        """
        self.runTool(text)
        fooVar = self.lookup.getKey("${foo}")
        self.assertIsInstance(fooVar.pointTo, CustomCommandNode)
        commandNode = fooVar.pointTo
        self.assertEqual("CONFIGURATION bar_config TARGET john_target PROJECT_NAME doe_project",
                         " ".join(getFlattedArguments(commandNode.pointTo[0])))

    def test_create_test_sourcelist_simple(self):
        text = """
        create_test_sourcelist(sourceListName driverName
                       test1 test2 test3
                       EXTRA_INCLUDE include.h
                       FUNCTION function)
        """
        self.runTool(text)
        self.assertEqual("sourceListName driverName test1 test2 test3 EXTRA_INCLUDE include.h FUNCTION function",
                         " ".join(getFlattedArguments(self.vmodel.findNode("create_test_sourcelist_0").pointTo[0])))

    def test_add_simple_test_first_sig_without_executable_command(self):
        text = """
        add_test(NAME mytest COMMAND testDriver --config enable_ai)
        """
        self.runTool(text)
        testNode = self.vmodel.findNode('mytest')
        self.assertIsInstance(testNode, TestNode)
        self.assertEqual("testDriver --config enable_ai", " ".join(getFlattedArguments(testNode.command)))

    def test_add_test_first_sig_without_executable_command_with_configuration(self):
        text = """
        add_test(NAME mytest COMMAND testDriver --config enable_ai
                             CONFIGURATIONS AMD
                             WORKING_DIRECTORY /program)
        """
        self.runTool(text)
        testNode = self.vmodel.findNode('mytest')
        self.assertIsInstance(testNode, TestNode)
        self.assertEqual("testDriver --config enable_ai", " ".join(getFlattedArguments(testNode.command)))
        self.assertEqual("AMD", " ".join(getFlattedArguments(testNode.configurations)))
        self.assertEqual("/program", " ".join(getFlattedArguments(testNode.working_directory)))

    def test_add_test_with_executable_command(self):
        text = """
        add_executable(foo bar.cxx)
        add_test(NAME mytest COMMAND foo --config enable_ai)
        """
        self.runTool(text)
        testNode = self.vmodel.findNode('mytest')
        self.assertEqual(self.lookup.getKey("t:foo"), testNode.command.getChildren()[0])

    def test_add_test_second_signature(self):
        text = """
        add_test(mytest doSth --config enable_ai)
        """
        self.runTool(text)
        testNode = self.vmodel.findNode('mytest')
        self.assertEqual("doSth --config enable_ai", " ".join(getFlattedArguments(testNode.command)))

    def test_cmake_host_system_information_without_condition(self):
        text = """
        cmake_host_system_information(RESULT foo QUERY HOSTNAME FQDN)
        """
        self.runTool(text)
        fooVar = self.lookup.getKey("${foo}")
        commandNode = fooVar.pointTo
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("HOSTNAME FQDN", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_get_filename_component_without_condition(self):
        text = """
        get_filename_component(foo bar.cxx DIRECTORY BASE_DIR /home)
        """
        self.runTool(text)
        fooVar = self.lookup.getKey("${foo}")
        a = flattenAlgorithmWithConditions(fooVar)
        self.assertIsInstance(fooVar,RefNode)
        self.assertEqual(1, len(a))
        self.assertEqual("/home", a[0][0])

    def test_get_property(self):
        text = """
        add_library(libB lib.cxx)
        get_property(INC_DIR_LIST TARGET libB PROPERTY INTERFACE_INCLUDE_DIRECTORIES SET)
        """
        self.runTool(text)
        varObject = self.lookup.getKey("${INC_DIR_LIST}")
        commandNode = varObject.pointTo
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(self.lookup.getKey("t:libB"),
                         commandNode.commands[0].getChildren()[1])

    def test_get_source_file_property_simple(self):
        text = """
        set(libFile lib.cxx)
        add_library(foo ${libFile})
        get_source_file_property(bar ${libFile} LOCATION)
        """
        self.runTool(text)
        barVar = self.lookup.getKey("${bar}")
        commandNode = barVar.pointTo
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("lib.cxx", commandNode.commands[0].getChildren()[0].pointTo.getValue())

    def test_get_target_property_simple(self):
        text = """
        set(libFile lib.cxx)
        add_library(foo ${libFile})
        get_target_property(bar foo COMPILE_FEATURES)
        """
        self.runTool(text)
        barVar = self.lookup.getKey("${bar}")
        commandNode = barVar.pointTo
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(self.lookup.getKey("t:foo"), commandNode.commands[0].getChildren()[0])

    def test_get_test_property_simple(self):
        text = """
        add_test(mytest doSth --config enable_ai)
        get_test_property(bar mytest DEPENDS)
        """
        self.runTool(text)
        barVar = self.lookup.getKey("${bar}")
        commandNode = barVar.pointTo
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(self.vmodel.findNode("mytest"), commandNode.commands[0].getChildren()[0])

    def test_export_targets_simple(self):
        text = """
        add_library(foo foo.cxx bar.cxx)
        add_library(john doe.cxx)
        export(TARGETS foo john NAMESPACE np FILE exported.cmake)
        """
        self.runTool(text)
        exportNode = self.vmodel.findNode('EXPORT')
        self.assertIsInstance(exportNode, CustomCommandNode)
        self.assertEqual(self.lookup.getKey("t:foo"), exportNode.commands[0].getChildren()[1])
        self.assertEqual(self.lookup.getKey("t:john"), exportNode.commands[0].getChildren()[2])

    def test_define_property(self):
        text = """
        define_property(DIRECTORY
                 PROPERTY PERMISSION
                 BRIEF_DOCS PermissionBriefDoc
                 FULL_DOCS PermissionFullDoc)
        """
        self.runTool(text)
        self.assertIn('PERMISSION', self.vmodel.definedProperties.get('DIRECTORY'))
        self.assertFalse(self.vmodel.definedProperties.get('DIRECTORY').get('PERMISSION').get('INHERITED'))

    def test_try_run(self):
        text = """
        try_run(RUN_RESULT
                COMPILE_RESULT
                ${CMAKE_CURRENT_BINARY_DIR}/library_magic_val
                "test_library_magic_val.c"
                RUN_OUTPUT_VARIABLE VAL_OUTPUT)
        """
        self.runTool(text)
        runVar = self.lookup.getKey("${RUN_RESULT}")
        compileVar = self.lookup.getKey("${COMPILE_RESULT}")
        runOutputVar = self.lookup.getKey("${VAL_OUTPUT}")
        commandNode = self.vmodel.findNode('try_run_0')
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(commandNode, runVar.pointTo)
        self.assertEqual(commandNode, compileVar.pointTo)
        self.assertEqual(commandNode, runOutputVar.pointTo)
        self.assertEqual("RUN_RESULT_VAR", runVar.relatedProperty)
        self.assertEqual("test_library_magic_val.c", commandNode.pointTo[0].getChildren()[1].getValue())

    def test_try_compile(self):
        text = """
        try_compile(RESULT_VAR binDir srcDir
                    testProject all
                    OUTPUT_VARIABLE OUT_VAR)
        """
        self.runTool(text)
        resultVar = self.lookup.getKey('${RESULT_VAR}')
        outVar = self.lookup.getKey("${OUT_VAR}")
        commandNode = self.vmodel.findNode('try_compile_0')
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(commandNode, resultVar.pointTo)
        self.assertEqual(commandNode, outVar.pointTo)
        self.assertEqual('RESULT_VAR', resultVar.relatedProperty)
        self.assertEqual('binDir srcDir testProject all', " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_target_sources_private_only_without_condition(self):
        text = """
        add_library(fooLib lib1.cxx)
        target_sources(fooLib PRIVATE lib2.cxx lib3.cxx)
        """
        self.runTool(text)
        fooLibTarget = self.lookup.getKey("t:fooLib")
        self.assertEqual("lib1.cxx lib2.cxx lib3.cxx", " ".join(getFlattedArguments(fooLibTarget.sources)))

    def test_target_compile_features_private_only_without_condition(self):
        text = """
        add_library(fooLib lib1.cxx lib2.cxx)
        target_compile_features(fooLib PRIVATE feature1 feature2)
        """
        self.runTool(text)
        fooLibTarget = self.lookup.getKey("t:fooLib")
        self.assertEqual("lib1.cxx lib2.cxx", " ".join(getFlattedArguments(fooLibTarget.sources)))
        self.assertEqual("feature1 feature2", " ".join(getFlattedArguments(fooLibTarget.compileFeatures)))

    def test_target_compile_options_private_only_without_condition(self):
        text = """
        add_library(fooLib lib1.cxx lib2.cxx)
        target_compile_options(fooLib PRIVATE option1 option2 PRIVATE option3)
        """
        self.runTool(text)
        fooLibTarget = self.lookup.getKey("t:fooLib")
        self.assertEqual("lib1.cxx lib2.cxx", " ".join(getFlattedArguments(fooLibTarget.sources)))
        self.assertEqual("option1 option2 option3", " ".join(getFlattedArguments(fooLibTarget.compileOptions)))

    def test_string_regex_match_without_condition(self):
        text = """
        set(foo bar)
        string(REGEX MATCH .* john ${foo})
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("REGEX MATCH .* bar", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_string_regex_replace_without_condition(self):
        text = """
        set(foo bar)
        string(REGEX REPLACE .* [a-b]* john ${foo})
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("REGEX REPLACE .* [a-b]* bar", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_string_replace_without_condition(self):
        text = """
        set(foo bar)
        string(REPLACE .* [a-b]* john ${foo} doe)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("REPLACE .* [a-b]* bar doe", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_string_concat_without_condition(self):
        text = """
        set(foo bar)
        string(CONCAT john ${foo} doe)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("CONCAT bar doe", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_string_compare_without_condition(self):
        text = """
        set(foo bar)
        string(COMPARE EQUAL ${foo} doe john)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("COMPARE EQUAL bar doe", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_string_ascii_without_condition(self):
        text = """
        string(ASCII 12 123 125 john)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("ASCII 12 123 125", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_string_tolower_without_condition(self):
        text = """
        string(TOLOWER Mehran john)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("TOLOWER Mehran", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_string_substring_without_condition(self):
        text = """
        string(SUBSTRING Mehran 0 2 john)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("SUBSTRING Mehran 0 2", " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_set_property_without_condition(self):
        text = """
        set(foo /bar)
        set_property(DIRECTORY ${foo} PROPERTY LABELS val1 val2)
        """
        self.runTool(text)
        setProperty = self.vmodel.findNode('set_property')
        self.assertEqual('DIRECTORY /bar PROPERTY LABELS val1 val2',
                         " ".join(getFlattedArguments(setProperty.commands[0])))

    def test_definition_directory_dependency(self):
        text = """
        add_library(foo foo.cpp)
        if(AMD)
            add_definitions(-Dboo)
            add_subdirectory(test_cmake_file/test_directory_definition)
        endif(AMD)
        """
        self.runTool(text)
        targetNode = self.vmodel.findNode('goo_2')
        commandNode = self.vmodel.findNode('add_definitions')
        self.assertIsInstance(commandNode, CommandDefinitionNode)
        self.assertEqual({'-Dboo', '-Dtest'}, set(map(lambda x: x[0], getFlattenedDefinitionsFromNode(targetNode.definitions))))
        flattened_result = printDefinitionsForATarget(self.vmodel, self.lookup, 'goo', output=True)
        self.assertSetEqual({'-Dboo'}, flattened_result['[AMD]'])
        self.assertSetEqual({'-Dtest'}, flattened_result['[AT_SUB, AMD]'])

    def test_add_definitions(self):
        text = """
        add_library(foo foo.cpp)
        if(ABC)
            add_definitions(-Dboo)
        endif(ABC)
        if(AMD)
            target_compile_definitions(foo PUBLIC boo)
        endif(AMD)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey('t:foo')
        commandNode = self.vmodel.findNode('add_definitions')
        self.assertIsInstance(commandNode, CommandDefinitionNode)
        self.assertEqual({'-Dboo'}, set(map(lambda x: x[0], getFlattenedDefinitionsFromNode(targetNode.definitions))))
        flattened_result = printDefinitionsForATarget(self.vmodel, self.lookup, 'foo', output=False)
        self.assertSetEqual({'-Dboo'}, flattened_result['[Or(ABC, AMD)]'])

    def test_target_definitions(self):
        text = """
        add_library(foo foo.cpp)
        target_compile_definitions(foo PUBLIC bar)
        target_compile_definitions(foo PRIVATE car)
        target_compile_definitions(foo INTERFACE far) 
        """
        self.runTool(text)
        targetNode = self.lookup.getKey('t:foo')
        self.assertIsInstance(targetNode, TargetNode)
        target_def = targetNode.definitions.getChildren()[0]
        interface_def = targetNode.interfaceDefinitions.getChildren()[0]
        self.assertIsInstance(target_def, DefinitionNode)
        self.assertIsInstance(interface_def, DefinitionNode)
        self.assertSetEqual({'-Dbar', '-Dcar'}, set(map(lambda x: x[0], getFlattenedDefinitionsFromNode(targetNode.definitions))))
        self.assertSetEqual({'-Dbar', '-Dfar'}, set(map(lambda x: x[0], getFlattenedDefinitionsFromNode(targetNode.interfaceDefinitions))))

    def test_remove_definitions(self):
        text = """
        add_library(foo foo.cpp)
        if(ABC)
        target_compile_definitions(foo PUBLIC bar)
        endif(ABC)
        add_definitions(/Dcar)
        if(AMD)
            remove_definitions(-Dbar -Dcar)
        endif(AMD)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey('t:foo')
        commandNode = self.vmodel.findNode('remove_definitions')
        self.assertIsInstance(commandNode, CommandDefinitionNode)
        self.assertEqual({'-Dbar', '-Dcar'}, set(map(lambda x: x[0], getFlattenedDefinitionsFromNode(targetNode.definitions))))
        flattened_result = printDefinitionsForATarget(self.vmodel, self.lookup, 'foo', output=False)
        self.assertSetEqual({'-Dbar'}, flattened_result['[ABC]'])
        self.assertSetEqual({'-Dcar'}, flattened_result['[Not(AMD)]'])


    def test_adding_subdirectory(self):
        text = """
        add_library(foo foo.cpp)
        add_subdirectory(test_cmake_file/test_subdirectory)        
        """
        self.runTool(text)
        targetNode = self.lookup.getVariableHistory('t:bar')[0]
        self.assertIsInstance(targetNode, TargetNode)

    def test_load_cache(self):
        text = """
        load_cache(/anotherproject READ_WITH_PREFIX
           foo entry1 entry2)
        """
        self.runTool(text)
        entry1Var = self.lookup.getKey('${fooentry1}')
        entry2Var = self.lookup.getKey('${fooentry2}')
        cacheCommand = entry1Var.getPointTo()
        self.assertIsInstance(cacheCommand, CustomCommandNode)
        self.assertEqual(cacheCommand, entry2Var.getPointTo())
        self.assertEqual('/anotherproject', cacheCommand.commands[0].getValue())

    def test_link_libraries(self):
        text = """
        add_library(foo bar.cxx)
        link_libraries(foo)
        add_executable(john doe.cxx)
        """
        self.runTool(text)
        johnTarget = self.lookup.getKey("t:john")
        fooTarget = self.lookup.getKey("t:foo")
        self.assertEqual(fooTarget, johnTarget.linkLibraries.getChildren()[0])
        self.assertEqual(fooTarget, self.vmodel.DIRECTORY_PROPERTIES.getKey('LINK_LIBRARIES').getChildren()[0])

    def test_link_directories(self):
        text = """
        link_directories(directory1 directory2)
        """
        self.runTool(text)
        self.assertEqual("directory1 directory2",
                         " ".join(getFlattedArguments(self.vmodel.DIRECTORY_PROPERTIES.getKey('LINK_DIRECTORIES')
                                                      .getChildren()[0])))

    def test_find_library_without_condition(self):
        text = """
        find_library(Magick++_LIBRARY
              NAMES Magick++
              PATHS /libraries
        )
        """
        self.runTool(text)
        foundVar = self.lookup.getKey('${Magick++_LIBRARY}')
        notFoundVar = self.lookup.getKey('${Magick++_LIBRARY-NOTFOUND}')
        commandNode = foundVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(commandNode, notFoundVar.getPointTo())
        self.assertEqual("NAMES Magick++ PATHS /libraries",
                         " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_find_package_without_condition(self):
        text = """
        find_package(Foo CONFIG REQUIRED)
        """
        with self.assertRaises(Exception) as context:
            self.runTool(text)

        self.assertTrue('Required package not found' in str(context.exception))

    def test_find_file_without_condition(self):
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
        find_program(Magick++_LIBRARY Magick++ /files)
        """
        self.runTool(text)
        foundVar = self.lookup.getKey('${Magick++_LIBRARY}')
        notFoundVar = self.lookup.getKey('${Magick++_LIBRARY-NOTFOUND}')
        commandNode = foundVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual(commandNode, notFoundVar.getPointTo())
        self.assertEqual("Magick++ /files",
                         " ".join(getFlattedArguments(commandNode.commands[0])))

    def test_include_without_condition(self):
        text = """
        set(foo bar)
        include(${foo} RESULT_VARIABLE john)
        """
        self.runTool(text)
        johnVar = self.lookup.getKey("${john}")
        commandNode = johnVar.getPointTo()
        self.assertIsInstance(commandNode, CustomCommandNode)
        self.assertEqual("bar", commandNode.depends[0].getPointTo().getValue())

    def test_simple_while_with_break_loop(self):
        text = """
        set(a foo)
        set(condition TRUE)
        while(condition)
          set(a ${a}bar)
          break()
          set(b mehran${a})
        endwhile()
        """
        self.runTool(text)
        self.assertIsInstance(self.lookup.getKey('${a}').pointTo, CustomCommandNode)
        self.assertIsInstance(self.lookup.getKey('${b}').pointTo, CustomCommandNode)
        customCommand = self.lookup.getKey('${b}').pointTo
        self.assertIn(self.lookup.getVariableHistory('${a}')[1], customCommand.pointTo)
        self.assertIn(self.lookup.getVariableHistory('${b}')[0], customCommand.pointTo)
        self.assertEqual(self.vmodel.findNode('break'), customCommand.pointTo[1])

    def test_target_include_directory_without_condition(self):
        text = """
        add_library(foo bar.cxx)
        target_include_directories(foo PRIVATE /private PUBLIC /public INTERFACE /interface)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey("t:foo")
        self.assertEqual("/private /public", " ".join(getFlattedArguments(targetNode.includeDirectories)))
        self.assertEqual("/public /interface", " ".join(getFlattedArguments(targetNode.interfaceIncludeDirectories)))

    def test_if_condition_on_variable_that_mutates(self):
        text = """
        set(foo ON)
        if(foo)
            set(john doe)
        endif(foo)
        set(foo OFF)
        
        if(foo)
            set(john doe2)
        endif(foo)
        """
        self.runTool(text)
        johnVersions = self.lookup.getVariableHistory('${john}')
        fooVersions = self.lookup.getVariableHistory('${foo}')
        firstSelectNode = johnVersions[0].getPointTo()
        secondSelectNode = johnVersions[1].getPointTo()
        self.assertEqual(fooVersions[0], firstSelectNode.args)
        self.assertEqual(fooVersions[1], secondSelectNode.args)

    def test_if_condition_on_option(self):
        text = """
        option(foo "something" ON)
        if(foo)
            set(john doe)
        endif()
        """
        self.runTool(text)
        fooVar = self.lookup.getKey('${foo}')
        johnVar = self.lookup.getKey('${john}')
        optionNode = fooVar.getPointTo()
        self.assertIsInstance(optionNode, OptionNode)
        self.assertEqual(fooVar, johnVar.getPointTo().args)

    def test_dependent_option(self):
        text = """
        option(USE_BAR "something" ON)
        option(USE_ZOT "something2" OFF)
        CMAKE_DEPENDENT_OPTION(USE_FOO "Use Foo" ON
                       "USE_BAR;NOT USE_ZOT" OFF)
        """
        self.runTool(text)
        fooVar = self.lookup.getKey("${USE_FOO}")
        barVar = self.lookup.getKey("${USE_BAR}")
        zotVar = self.lookup.getKey("${USE_ZOT}")
        fooOption = fooVar.getPointTo()
        self.assertIsInstance(fooOption, OptionNode)
        self.assertEqual(barVar, fooOption.depends.getChildren()[0])
        self.assertEqual(zotVar, fooOption.depends.getChildren()[2])

    @unittest.skip("")
    def test_target_link_libraries(self):
        text = """
        set(RENDERER_LIBRARIES lib1 lib2)
        if(NOT APPLE)
            set(R1_NAME renderer_opengl1_${ARCH})
        else()
            set(R1_NAME renderer_opengl1${LIB_SUFFIX})
        endif()
        
        if(MSVC)
            target_link_libraries(${R1_NAME} ${RENDERER_LIBRARIES})
        else()
            target_link_libraries(${R1_NAME} ${RENDERER_LIBRARIES} 'm')
        endif(MSVC)
        """
        self.runTool(text)

    # This is deprecated due to new target definition architecture
    @unittest.skip("")
    def test_target_compile_definition(self):
        text = """
        add_executable(foo bar.cxx)
        if(APPLE)
            target_compile_definitions(foo PUBLIC item1 item2)
        endif()
        """
        self.runTool(text)
        fooTarget = self.lookup.getKey("t:foo")
        self.assertIsInstance(fooTarget, TargetNode)
        definitionNode = fooTarget.getDefinition()
        self.assertIsInstance(definitionNode, SelectNode)
        self.assertIsInstance(definitionNode.trueNode, ConcatNode)
        self.assertEqual("PUBLIC item1 item2", " ".join(getFlattedArguments(definitionNode.trueNode)))

    def test_make_dependency_to_a_file_before_generated(self):
        text = """
        add_custom_target(mod_pk3 ALL DEPENDS foo)
        add_custom_command(OUTPUT foo COMMAND john)
        """
        self.runTool(text)
        targetNode = self.lookup.getKey("t:mod_pk3")
        self.assertIsInstance(targetNode, TargetNode)
        fooNode = targetNode.sources.getChildren()[0]
        self.assertIsInstance(fooNode, RefNode)
        self.assertIsInstance(fooNode.getPointTo(), CustomCommandNode)

    @unittest.skip("")
    def test_foreach_list_without_condition(self):
        text = """
        set(lstVar foo bar john doe)
        set(lstvarb mehran meidani)
        set(listVar 1 2)
        foreach(var IN LISTS lstVar lstvarb ITEMS "Sample Item")
          list(APPEND listVar ${var})
        endforeach(var)
        """
        self.runTool(text)

    @unittest.skip("")
    def test_foreach_list_with_option_and_condition(self):
        text = """
        option(op1 Yes)
        if(op1)
           set(varA foo bar)
        else()
           set(varA john doe)
        endif()
        set(listVar 1 2)
        foreach(var IN LISTS varA)
          list(APPEND listVar ${var})
        endforeach(var)
        """
        self.runTool(text)

    @unittest.skip("")
    def test_foreach_simple_usage(self):
        text = """
        set(foo bar john doe)
        foreach(argument ${foo})
          set(bar ${argument})
        endforeach()
        """
        self.runTool(text)

    def test_variable_dependency_without_function(self):
        text = """
        option(foo "Is bar?" YES)
        if(foo)
            set(base_dir /foo)
        else()
            set(base_dir /bar)
        endif()
        
        if(NOT source_file)
            set(path ${base_dir}/src/*.cxx)
        else()
            set(path ${base_dir}/src/${source_file})
        endif()
        
        FILE(GLOB lib_files
            ${path}
        )
        """
        self.runTool(text)
        pathVar = self.lookup.getKey("${path}")

        # self.vmodel.export()

    def test_a_sample_for_simple_variable_dependent(self):
        text = """
        option(foo "Is bar?" YES)
        if(foo)
            set(base_dir files_for_test)
        else()
            set(base_dir another_folder_for_test)
        endif()
        
        if(NOT source_file)
            set(path ${base_dir}/*.cxx)
        else()
            set(path ${base_dir}/a.cxx)
        endif()
            
        add_executable(test_exec ${path})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'test_exec', False)
        self.assertEqual(4, len(a))
        self.assertSetEqual({"another_folder_for_test/b2.cxx",
                             "another_folder_for_test/a.cxx"}, a['[Not(source_file), Not(foo)]'])
        self.assertSetEqual({"files_for_test/a.cxx",
                             "files_for_test/b.cxx", "files_for_test/c.cxx"}, a['[Not(source_file), foo]'])

    def test_runtime_graph_with_file_command(self):
        text = """
        option(foo "Is bar?" YES)
        
        if(foo)
            set(path files_for_test/*.cxx)
        else()
            set(path files_for_test/a.cxx)
        endif()

        FILE(GLOB lib_files
            ${path}
        )
        
        add_executable(test_exec ${lib_files})
        """
        self.runTool(text)
        commandNode = self.lookup.getKey("${lib_files}").getPointTo()
        assert isinstance(commandNode, CustomCommandNode)

        # buildRuntimeGraph(self.vmodel, self.lookup)
        a = printFilesForATarget(self.vmodel, self.lookup, 'test_exec')
        self.assertIn('./files_for_test/a.cxx', a['[Not(foo)]'])
        self.assertSetEqual({'./files_for_test/a.cxx', "./files_for_test/c.cxx", "./files_for_test/b.cxx"}, a['[foo]'])

    def test_get_files_for_a_target_with_dependency_to_other_target(self):
        text = """
        option(foo "Is bar?" YES)
        option(john "Or John?" NO)
        if(foo)
            set(path files_for_test/*.cxx)
        else()
            set(path files_for_test/a.cxx)
        endif()
        FILE(GLOB lib_files
            ${path}
        )
        add_library(test_library ${lib_files})
        add_executable(test_exec another_folder_for_test/*.cxx)
        add_executable(test_exec_john another_folder_for_test/a.cxx)
        
        if(john)
            set(test_t test_exec)
        else()
            set(test_t test_exec_john)
        endif()
        
        target_link_libraries(${test_t} PUBLIC test_library)
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'test_exec_john')
        self.assertSetEqual({"another_folder_for_test/a.cxx"}, a["[]"])
        self.assertSetEqual({"./files_for_test/a.cxx"}, a['[Not(foo), Not(john)]'])
        self.assertSetEqual({"./files_for_test/c.cxx",
                             "./files_for_test/b.cxx",
                             "./files_for_test/a.cxx"}, a['[Not(john), foo]'])

    def test_get_files_for_a_target_with_dependency_to_other_target_concatinated_target_name(self):
        text = """
        option(foo "Is bar?" YES)
        option(john "Or John?" NO)
        if(foo)
            set(path files_for_test/*.cxx)
        else()
            set(path files_for_test/a.cxx)
        endif()
        FILE(GLOB lib_files
            ${path}
        )
        add_library(test_library ${lib_files})
        add_executable(test_exec another_folder_for_test/*.cxx)
        add_executable(test_exec_john another_folder_for_test/a.cxx)

        if(john)
            set(test_t _exec)
        else()
            set(test_t _exec_john)
        endif()

        target_link_libraries(test${test_t} PUBLIC test_library)
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'test_exec_john')
        self.assertSetEqual({"another_folder_for_test/a.cxx"}, a["[]"])
        self.assertSetEqual({"./files_for_test/a.cxx"}, a['[Not(foo), Not(john)]'])
        self.assertSetEqual({"./files_for_test/c.cxx",
                             "./files_for_test/b.cxx",
                             "./files_for_test/a.cxx"}, a['[Not(john), foo]'])

    def test_cycle_detection_system_works(self):
        text = """
        add_executable(foo another_folder_for_test/*.cxx)
        add_executable(bar another_folder_for_test/a.cxx)
        set(targeta oo)
        target_link_libraries(f${targeta} PUBLIC bar)
        target_link_libraries(bar PUBLIC foo)
        """
        self.runTool(text)
        self.assertRaises(CycleDetectedException, printFilesForATarget, self.vmodel, self.lookup, 'foo')

    def test_flatten_file_for_a_target_from_a_list(self):
        text = """
        add_library(foo another_folder_for_test/*.cxx)
        add_library(bar files_for_test/a.cxx)
        LIST(APPEND CLIENT_LIBRARIES foo bar)
        add_executable(john files_for_test/b.cxx)
        target_link_libraries(john ${CLIENT_LIBRARIES})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'john', False)
        self.assertSetEqual({"files_for_test/a.cxx", "another_folder_for_test/a.cxx",
                             "files_for_test/b.cxx", "another_folder_for_test/b2.cxx"}, a['[]'])

    def test_flatten_file_for_a_target_from_a_list_with_literal_concat(self):
        text = """
        add_library(foo another_folder_for_test/*.cxx)
        add_library(bar files_for_test/a.cxx)
        LIST(APPEND CLIENT_LIBRARIES foo bar)
        add_executable(john files_for_test/b.cxx)
        set(varA jo)
        target_link_libraries(${varA}hn ${CLIENT_LIBRARIES})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'john', False)
        self.assertSetEqual({"files_for_test/a.cxx", "another_folder_for_test/a.cxx",
                             "files_for_test/b.cxx", "another_folder_for_test/b2.cxx"}, a['[]'])

    def test_flatten_file_with_else_if_condition(self):
        text = """
        option(foo "Is bar?" YES)
        option(john "Is jon?" YES)
        if(foo)
            set(libraries files_for_test/a.cxx files_for_test/b.cxx)
        elseif(NOT john)
            set(libraries files_for_test/c.cxx)
        else()
            set(libraries another_folder_for_test/*.cxx)
        endif()
        add_executable(exec ${libraries})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        self.assertSetEqual({"another_folder_for_test/b2.cxx", "another_folder_for_test/a.cxx"},
                            a['[Not(foo), john]'])
        self.assertSetEqual({"files_for_test/a.cxx", "files_for_test/b.cxx"},
                            a['[foo]'])
        self.assertSetEqual({"files_for_test/c.cxx"},
                            a['[Not(foo), Not(john)]'])

    def test_flatten_target_with_link_libraries_and_else_if(self):
        text = """
        option(foo "Is bar?" YES)
        option(john "Is john?" YES)
        add_executable(exec files_for_test/a.cxx files_for_test/b.cxx)
        add_library(lib1 files_for_test/c.cxx)
        add_library(lib2 another_folder_for_test/a.cxx)
        add_library(lib3 another_folder_for_test/*.cxx)
        if(foo)
            target_link_libraries(exec lib1)
        elseif(NOT john)
            target_link_libraries(exec lib2)
        else()
            target_link_libraries(exec lib3)
        endif()
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        self.assertSetEqual({"files_for_test/b.cxx", "files_for_test/a.cxx"}, a["[]"])
        self.assertSetEqual({"another_folder_for_test/b2.cxx", "another_folder_for_test/a.cxx"},
                            a['[Not(foo), john]'])
        self.assertSetEqual({"another_folder_for_test/a.cxx"}, a['[Not(foo), Not(john)]'])
        self.assertSetEqual({"files_for_test/c.cxx"}, a['[foo]'])

    def test_flatten_target_with_nested_if_statements(self):
        text = """
        option(foo "Is bar?" YES)
        option(john "Is john?" YES)
        add_executable(exec files_for_test/a.cxx files_for_test/b.cxx)
        add_library(lib another_folder_for_test/*.cxx)
        if(foo)
            if(john)
                target_link_libraries(exec lib)
            endif()
        endif()
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        self.assertSetEqual({"files_for_test/a.cxx", "files_for_test/b.cxx"},
                            a["[]"])

        self.assertSetEqual({"another_folder_for_test/b2.cxx", "another_folder_for_test/a.cxx"},
                            a['[john, foo]'])

    def test_flatten_target_with_variable_inside_nested_if_statements(self):
        text = """
        option(foo "Is bar?" YES)
        option(john "Is john?" YES)
        set(libraries files_for_test/a.cxx)
        if(foo)
            set(libraries files_for_test/c.cxx)
            if(john)
                set(libraries files_for_test/a.cxx files_for_test/b.cxx)
            else()
                set(libraries another_folder_for_test/*.cxx)
            endif()
        endif()
        add_executable(exec ${libraries})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        self.assertSetEqual({"files_for_test/a.cxx"}, a['[Not(foo)]'])
        self.assertSetEqual({"another_folder_for_test/a.cxx",
                             "another_folder_for_test/b2.cxx"}, a['[Not(john), foo]'])
        self.assertSetEqual({"files_for_test/b.cxx",
                             "files_for_test/a.cxx"}, a['[foo, john]'])

    def test_simple_if_assignment_outside_if(self):
        text = """
        option(foo "Is bar?" YES)
        set(libraries files_for_test/a.cxx)
        if(foo)
            set(libraries files_for_test/b.cxx)
        endif()
        add_executable(exec ${libraries})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        self.assertSetEqual({"files_for_test/a.cxx"}, a["[Not(foo)]"])
        self.assertSetEqual({"files_for_test/b.cxx"}, a["[foo]"])

    def test_nested_if_statement_append_list(self):
        text = """
        option(BUILD_SERVER "des1" YES)
        option(FEATURE_IRC_SERVER "des2" YES)
        set(SERVER_SRC files_for_test/a.cxx)
        if(BUILD_SERVER)
            if(FEATURE_IRC_SERVER)
                list(APPEND SERVER_SRC files_for_test/b.cxx)
            endif(FEATURE_IRC_SERVER)
        endif(BUILD_SERVER)
        add_executable(exec ${SERVER_SRC})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        self.assertSetEqual({"files_for_test/b.cxx", "files_for_test/a.cxx"}, a['[BUILD_SERVER, FEATURE_IRC_SERVER]'])
        self.assertIn('files_for_test/a.cxx', a['[BUILD_SERVER, Not(FEATURE_IRC_SERVER)]'])
        self.assertIn('files_for_test/a.cxx', a['[Not(BUILD_SERVER)]'])

    def test_nested_if_statement_with_else_append_list(self):
        text = """
        option(BUILD_SERVER "des1" YES)
        option(FEATURE_IRC_SERVER "des2" YES)
        set(SERVER_SRC files_for_test/a.cxx)
        if(BUILD_SERVER)
            if(FEATURE_IRC_SERVER)
                list(APPEND SERVER_SRC files_for_test/b.cxx)
            else()
                list(APPEND SERVER_SRC files_for_test/c.cxx)
            endif(FEATURE_IRC_SERVER)
        else()
            list(APPEND SERVER_SRC another_folder_for_test/a.cxx)
        endif(BUILD_SERVER)
        add_executable(exec ${SERVER_SRC})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        self.assertSetEqual({"files_for_test/a.cxx", "another_folder_for_test/a.cxx"}, a['[Not(BUILD_SERVER)]'])
        self.assertIn("files_for_test/a.cxx", a['[BUILD_SERVER, Not(FEATURE_IRC_SERVER)]'])
        self.assertIn("files_for_test/a.cxx", a['[BUILD_SERVER, FEATURE_IRC_SERVER]'])

        self.assertIn("files_for_test/b.cxx", a['[BUILD_SERVER, FEATURE_IRC_SERVER]'])
        self.assertIn("files_for_test/c.cxx", a['[BUILD_SERVER, Not(FEATURE_IRC_SERVER)]'])

    def test_list_remove_variable(self):
        text = """
        set(foo a b c)
        list(REMOVE_ITEM foo b)
        """
        self.runTool(text)
        listVar = self.lookup.getKey('${foo}')
        a = flattenAlgorithmWithConditions(listVar)
        self.assertCountEqual([('a', set()), ('c', set())], a)

    def test_variable_growth(self):
        text = """
        option(opt1 "des" YES)
        option(opt2 "des" YES)
        
        set(var_a foo bar john doe)
        if(opt1)
            list(APPEND var_a files_for_test/a.cxx)
        elseif(opt2)
            list(APPEND var_a files_for_test/*.cxx)
        else()
            list(APPEND var_a files_for_test/c.cxx)
        endif()
        
        if(opt2)
            list(append var_a mehran)
        elseif(NOT opt1 AND opt2)
            list(append var_a meidani)
        else()
            list(append var_a farshad)
        endif()
        
        
        add_executable(exec ${var_a})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec', False)
        # print(a)

    def test_concat_node_with_multiple_condition(self):
        text = """
        option(opt1 "des" YES)
        option(opt2 "des" YES)
        
        set(foo john)
        set(bar doe)
        if(opt1)
            set(foo opt1_john)
        endif()
        if(opt2)
            set(bar opt2_doe)
        endif()
        
        add_executable(exec ${foo} ${bar})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec')
        self.assertIn('john', a['[opt2, Not(opt1)]'])
        self.assertIn('john', a['[Not(opt2), Not(opt1)]'])

        self.assertIn('opt2_doe', a['[opt2, Not(opt1)]'])
        self.assertIn('opt2_doe', a['[opt2, opt1]'])

    def test_string_concat_node_with_multiple_condition(self):
        text = """
        option(opt1 "des" YES)
        option(opt2 "des" YES)

        set(foo john)
        set(bar doe)
        if(opt1)
            set(foo opt1_john)
        endif()
        if(opt2)
            set(bar opt2_doe)
        endif()

        set(baz ${foo}/${bar})
        """
        self.runTool(text)
        bazVar = self.lookup.getKey('${baz}')
        a = flattenAlgorithmWithConditions(bazVar)
        postprocessZ3Output(a)
        result = []
        for item in a:
            result.append((item[0], str(item[1])))
        self.assertEqual(4, len(result))
        self.assertIn(('john/doe', '[Not(opt2), Not(opt1)]'), result)
        self.assertIn(('john/opt2_doe', '[opt2, Not(opt1)]'), result)
        self.assertIn(('opt1_john/doe', '[Not(opt2), opt1]'), result)
        self.assertIn(('opt1_john/opt2_doe', '[opt2, opt1]'), result)

    def test_string_concat_node_with_multiple_condition_not_first_condition(self):
        text = """
        option(opt1 "des" YES)
        option(opt2 "des" YES)

        set(foo john)
        set(bar doe)
        if(opt1)
            set(foo opt1_john)
        endif()
        if(opt2 AND NOT opt1)
            set(bar opt2_doe)
        endif()

        set(baz ${foo}/${bar})
        add_executable(exec ${baz})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec')
        self.assertEqual(3, len(a))
        self.assertIn('john/doe', a['[Not(opt2), Not(opt1)]'])
        self.assertIn('john/opt2_doe', a['[opt2, Not(opt1)]'])
        self.assertIn('opt1_john/doe', a['[opt1]'])

    def test_z_real_ecm_mark_as_test(self):
        text = """
        if (NOT BUILD_TESTING)
            if(NOT TARGET buildtests)
                add_custom_target(buildtests)
            endif()
        endif()

        function(ecm_mark_as_test)
            if (NOT BUILD_TESTING)
                foreach(_target ${ARGN})
                    set_target_properties(${_target}
                                            PROPERTIES
                                            EXCLUDE_FROM_ALL TRUE
                                        )
                    add_dependencies(buildtests ${_target})
                endforeach()
            endif()
        endfunction()
        
        add_executable(exec files_for_test/a.cxx)
        ecm_mark_as_test(exec)
        """
        self.runTool(text)
        # self.vmodel.export(False, True)

    def test_GREATER_2_if_condition(self):
        text = """
        set(doe 1)
        if (doe GREATER 3)
            set(foo bar.cpp)
        else()
            if(doe GREATER 5)
                set(foo john.cpp)
            else()
                set(foo doe.cpp)
            endif()
        endif()
        add_executable(exec ${foo})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec')
        self.assertEqual(1, len(a.keys()))
        self.assertIn('doe.cpp', a['[doe == 1]'])

    def test_GREATER_3_if_condition(self):
        text = """
        if(APPLE)
            set(doe 5)
        else()
            set(doe 2)
        endif()
        
        if (doe GREATER 3)
            set(foo bar.cpp)
        else()
            if(doe GREATER 1)
                set(foo john.cpp)
            else()
                set(foo doe.cpp)
            endif()
        endif()
        add_executable(exec ${foo})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec')

        self.assertEqual(2, len(a.keys()))
        self.assertIn('john.cpp', a['[Not(APPLE), doe == 2]'])
        self.assertIn('bar.cpp', a['[APPLE, doe == 5]'])

    def test_GREATER_variable_if_condition(self):
        text = """
        set(doe 1)
        set(three 3)
        if (doe GREATER three)
            set(foo bar.cpp)
        else()
            set(foo john.cpp)
        endif()
        add_executable(exec ${foo})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec')
        self.assertEqual(1, len(a.keys()))
        self.assertIn('john.cpp', a['[doe == 1, three == 3]'])

    def test_string_match(self):
        text = """
        set(foo mehran)
        set(john no_doe)
        if(foo STREQUAL mehran)
            set(john doe)
        endif()
        """
        self.runTool(text)
        johnVar = self.lookup.getKey('${john}')
        a = flattenAlgorithmWithConditions(johnVar)
        postprocessZ3Output(a)
        self.assertEqual(1, len(a))
        self.assertEqual('doe', a[0][0])

    def test_boolean_arithmetic_int_expression(self):
        text = """
        option(USE_CURL something 1)
        if(USE_CURL)
            set(foo 4)
        else()
            set(foo 1)
        endif()
        
        set(john mehran)
        set(result 1)
        
        if(APPLE AND foo GREATER 2)
            if(MAC OR LINUX AND john STREQUAL mehran)
                set(result 2)
            endif()
        endif()
        """
        self.runTool(text)
        resultVar = self.lookup.getKey('${result}')
        a = flattenAlgorithmWithConditions(resultVar)
        postprocessZ3Output(a)
        self.assertEqual(4, len(a))

    def test_symbolic_evaluation(self):
        text = """
        set(GRPC_OUT_PRE_PATH ${CMAKE_BINARY_DIR}/grpc)
        set(CONTAINER_PROTOS_OUT_PATH ${GRPC_OUT_PRE_PATH}/src/api/services/containers)
        """
        self.runTool(text)
        var = self.lookup.getKey('${CONTAINER_PROTOS_OUT_PATH}')
        a = flattenAlgorithmWithConditions(var)
        postprocessZ3Output(a)
        self.assertEqual('CMAKE_BINARY_DIR/grpc/src/api/services/containers', a[0][0])

    def test_flatten_symbolic_concat_node(self):
        text = """
        aux_source_directory(${CMAKE_BINARY_DIR}/grpc/src/api/services/containers baz)
        set(foo bar.cpp)
        file(GLOB john files_for_test/*.cxx)
        add_executable(exec ${baz} ${foo} ${john})
        add_executable(exec2 ${baz} ${john} ${foo})
        
        add_executable(exec3 ${john} ${foo} ${baz})
        add_executable(exec4 ${john} ${baz} ${foo})
        
        add_executable(exec5 ${foo} ${john} ${baz})
        add_executable(exec6 ${foo} ${baz} ${john})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec')
        b = printFilesForATarget(self.vmodel, self.lookup, 'exec2')
        c = printFilesForATarget(self.vmodel, self.lookup, 'exec3')
        d = printFilesForATarget(self.vmodel, self.lookup, 'exec4')
        e = printFilesForATarget(self.vmodel, self.lookup, 'exec5')
        f = printFilesForATarget(self.vmodel, self.lookup, 'exec6')
        self.assertTrue(a == b == c == d == e == f)

    def test_flatten_symbolic_conditional_concat_node(self):
        text = """    
        set(foo bar.cpp)
        
        option(build_client "" yes)
        option(build_server "" yes)
        if(build_server)
            aux_source_directory(${CMAKE_BINARY_DIR}/grpc/src/api/services/containers server_src)
        endif()
        
        if(build_client)
            file(GLOB client_src files_for_test/*.cxx)
        endif()
        
        add_executable(exec ${foo} ${server_src} ${client_src})
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'exec')
        self.assertSetEqual({'bar.cpp'}, a['[]'])
        self.assertSetEqual({'./files_for_test/a.cxx',
                             'bar.cpp',
                             'CMAKE_BINARY_DIR/grpc/src/api/services/containers',
                             './files_for_test/b.cxx',
                             './files_for_test/c.cxx'}, a['[build_client, build_server]'])

    def test_simple_target_name_as_variable(self):
        text = """
        SET(EXE foo)
        add_executable(${EXE} bar.c)
        """
        self.runTool(text)
        self.assertIsNotNone(self.lookup.getKey('t:foo'))
        self.assertIsInstance(self.lookup.getKey('t:foo'), TargetNode)
        a = printFilesForATarget(self.vmodel, self.lookup, 'foo')
        self.assertSetEqual({'bar.c'}, a['[]'])

    def test_simple_target_link_library_target_name_as_variable(self):
        text = """
        set(EXE foo)
        add_executable(${EXE} bar.c)
        add_executable(john doe.c)
        target_link_libraries(${EXE} john)
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'foo')
        self.assertSetEqual({'bar.c', 'doe.c'}, a['[]'])

    def test_conditional_target_name_as_variable(self):
        text = """
        if(APPLE)
            set(EXE foo)
        else()
            set(EXE bar)
        endif()
        add_executable(${EXE} bar.c)
        """
        self.runTool(text)
        self.assertIsNotNone(self.lookup.getKey('t:foo'))
        self.assertIsInstance(self.lookup.getKey('t:foo'), TargetNode)
        self.assertIsNotNone(self.lookup.getKey('t:bar'))
        self.assertIsInstance(self.lookup.getKey('t:bar'), TargetNode)
        a = printFilesForATarget(self.vmodel, self.lookup, 'foo')
        b = printFilesForATarget(self.vmodel, self.lookup, 'bar')
        self.assertSetEqual({'bar.c'}, a['[APPLE]'])
        self.assertSetEqual({'bar.c'}, b['[Not(APPLE)]'])

    def test_conditional_target_name_as_variable_2(self):
        text = """
        if(APPLE)
            set(EXE foo)
            add_executable(${EXE} foo.c)
        else()
            set(EXE bar)
            add_executable(${EXE} bar.c)
        endif()
        """
        self.runTool(text)
        self.assertIsNotNone(self.lookup.getKey('t:foo'))
        self.assertIsInstance(self.lookup.getKey('t:foo'), TargetNode)
        self.assertIsNotNone(self.lookup.getKey('t:bar'))
        self.assertIsInstance(self.lookup.getKey('t:bar'), TargetNode)
        a = printFilesForATarget(self.vmodel, self.lookup, 'foo')
        b = printFilesForATarget(self.vmodel, self.lookup, 'bar')
        self.assertSetEqual({'foo.c'}, a['[APPLE]'])
        self.assertSetEqual({'bar.c'}, b['[Not(APPLE)]'])

    def test_simple_target_link_library_target_name_as_variable_conditional(self):
        text = """
        if(APPLE)
            set(EXE foo)
        else()
            set(EXE bar)
        endif()
        add_executable(${EXE} bar.c)
        
        add_executable(john doe.c)
        target_link_libraries(${EXE} john)
        """
        self.runTool(text)
        a = printFilesForATarget(self.vmodel, self.lookup, 'foo')
        b = printFilesForATarget(self.vmodel, self.lookup, 'bar')
        self.assertSetEqual({'bar.c', 'doe.c'}, a['[APPLE]'])
        self.assertSetEqual({'bar.c', 'doe.c'}, b['[Not(APPLE)]'])

    def test_project_gloabl_variables(self):
        text = """    
        set(KALARM_VERSION "3.2.1")

        project(kalarm VERSION ${KALARM_VERSION})
        """
        self.runTool(text)
        projectSourceDir = self.lookup.getKey('${kalarm_VERSION}')
        self.assertEqual(projectSourceDir.pointTo.getValue(),'${KALARM_VERSION}')

    def test_prevent_stacking_double_quotation(self):
        text = """    
        set(a "test")
        set(b "${a}")
        set(cVar "${b}" )
        set(dVar "${cVar}/test" )
        """
        self.runTool(text)
        cVar = self.lookup.getKey('${cVar}')
        a = flattenAlgorithmWithConditions(cVar)
        self.assertEqual('test', a[0][0])
        dVar = self.lookup.getKey('${dVar}')
        b = flattenAlgorithmWithConditions(dVar)
        self.assertEqual('test/test', b[0][0])


    def test_ECM_config(self):
        text= """
        get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

        macro(set_and_check _var _file)
          set(${_var} "${_file}")
          if(NOT EXISTS "${_file}")
            message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
          endif()
        endmacro()
        
        macro(check_required_components _NAME)
          foreach(comp ${${_NAME}_FIND_COMPONENTS})
            if(NOT ${_NAME}_${comp}_FOUND)
              if(${_NAME}_FIND_REQUIRED_${comp})
                set(${_NAME}_FOUND FALSE)
              endif()
            endif()
          endforeach()
        endmacro()
        
        ####################################################################################
        
        set(ECM_FIND_MODULE_DIR "${PACKAGE_PREFIX_DIR}/share/ECM/find-modules/")
        
        set(ECM_MODULE_DIR "${PACKAGE_PREFIX_DIR}/share/ECM/modules/")
        
        set(ECM_KDE_MODULE_DIR "${PACKAGE_PREFIX_DIR}/share/ECM/kde-modules/")
        
        set(ECM_PREFIX "${PACKAGE_PREFIX_DIR}")
        
        set(ECM_MODULE_PATH "${ECM_MODULE_DIR}" "${ECM_FIND_MODULE_DIR}" "${ECM_KDE_MODULE_DIR}")
        
        set(ECM_GLOBAL_FIND_VERSION "${ECM_FIND_VERSION}")
        """
        self.runTool(text)
        ECM_FIND_MODULE_DIR = self.lookup.getKey('${ECM_FIND_MODULE_DIR}')
        a = flattenAlgorithmWithConditions(ECM_FIND_MODULE_DIR)
        self.assertEqual('/../../../share/ECM/find-modules/', a[0][0])
        ECM_MODULE_PATH = self.lookup.getKey('${ECM_MODULE_PATH}')
        b = flattenAlgorithmWithConditions(ECM_MODULE_PATH)
        self.assertEqual('/../../../share/ECM/kde-modules/', b[0][0])
        self.assertEqual('/../../../share/ECM/find-modules/', b[1][0])
        self.assertEqual('/../../../share/ECM/modules/', b[2][0])

    def test_PROJECT_SOURCE_DIR(self):
        text = """    
        set(KF5_MIN_VERSION "5.82.0")
        set(KALARM_VERSION "3.2.1")

        project(kalarm VERSION ${KALARM_VERSION})
        """
        self.runTool(text)
        kalarm_SOURCE_DIR = self.lookup.getKey('${kalarm_SOURCE_DIR}')
        a = flattenAlgorithmWithConditions(kalarm_SOURCE_DIR)
        self.assertEqual('', a[0][0])

    def test_finding_package_config_mode_cmake_file(self):
        text = """    
        set(KF5_MIN_VERSION "5.82.0")
        set(KALARM_VERSION "3.2.1")

        project(kalarm VERSION ${KALARM_VERSION})
        
        find_package(ECM ${KF5_MIN_VERSION} CONFIG REQUIRED)
        set(CMAKE_MODULE_PATH ${kalarm_SOURCE_DIR}/cmake/modules ${ECM_MODULE_PATH})
        """
        self.runTool(text)
        CMAKE_MODULE_PATH = self.lookup.getKey('${CMAKE_MODULE_PATH}')
        a = flattenAlgorithmWithConditions(CMAKE_MODULE_PATH)
        self.assertEqual('/usr/share/ECM/cmake/../../../share/ECM/kde-modules/', a[0][0])
        self.assertEqual('/cmake/modules', a[1][0])
        self.assertEqual('/usr/share/ECM/cmake/../../../share/ECM/find-modules/', a[2][0])
        self.assertEqual('/usr/share/ECM/cmake/../../../share/ECM/modules/', a[3][0])

    def test_conditional_find_package(self):
        text = """    
        set(var CheckFortranSourceRuns)
        if(APPLE)
          set(var ECM)
        endif(APPLE )
        find_package(${var})
        """
        self.runTool(text)
        ECM_PREFIX = self.lookup.getKey('${ECM_PREFIX}')
        a = flattenAlgorithmWithConditions(ECM_PREFIX)
        self.assertEqual('/usr/share/ECM/cmake/../../..', a[0][0])
        self.assertEqual('{APPLE}', str(a[0][1]))
        self.assertEqual(1, len(a))
if __name__ == '__main__':
    unittest.main()
