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
        self.assertIn('../../../share/ECM/kde-modules/', a[0][0])
        self.assertEqual('./cmake/modules', a[1][0])
        self.assertIn('../../../share/ECM/find-modules/', a[2][0])
        self.assertIn('../../../share/ECM/modules/', a[3][0])



    def test_dependent_include(self):
        text = """    
        cmake_minimum_required( VERSION 3.0 )
        
        set(SNORE_VERSION_MAJOR 0)
        set(SNORE_VERSION_MINOR 7)
        set(SNORE_VERSION_PATCH 1)
        
        project( SnoreNotify VERSION "${SNORE_VERSION_MAJOR}.${SNORE_VERSION_MINOR}.${SNORE_VERSION_PATCH}" )
        
        include(FeatureSummary)
        
        find_package(ECM 1.7.0 REQUIRED NO_MODULE)
        
        set(CMAKE_MODULE_PATH ${ECM_MODULE_PATH} ${ECM_KDE_MODULE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules )
        """
        self.runTool(text)


if __name__ == '__main__':
    unittest.main()
