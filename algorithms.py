import glob
import logging
import os
import re
from collections import Set, defaultdict
from typing import Dict, List
from z3 import *

from datastructs import DefinitionNode, Node, LiteralNode, RefNode, CustomCommandNode, SelectNode, ConcatNode, TargetNode, OptionNode
from vmodel import VModel


directory_definition_stack = {}


def flattenAlgorithm(node: Node):
    if isinstance(node, LiteralNode):
        return [node.getValue()]
    elif isinstance(node, RefNode):
        # If RefNode is a symbolic node, it may not have point to attribute
        if node.getPointTo() is None:
            if '_' in node.getName():
                return node.getName()[:node.getName().rindex('_')]
            return node.getName()
        return flattenAlgorithm(node.getPointTo())
    elif isinstance(node, CustomCommandNode):
        result = []
        for child in node.getChildren():
            result += flattenAlgorithm(child)
        return result
    elif isinstance(node, SelectNode):
        if node.falseNode and node.trueNode:
            return flattenAlgorithm(node.falseNode) + flattenAlgorithm(node.trueNode)
        if node.trueNode:
            return flattenAlgorithm(node.trueNode)
        if node.falseNode:
            return flattenAlgorithm(node.falseNode)
    elif isinstance(node, ConcatNode):
        result = {''}
        for item in node.getChildren():
            childSet = flattenAlgorithm(item)
            tempSet = set()
            for str1 in result:
                for str2 in childSet:
                    if str1 == '':
                        tempSet.add(str2)
                    else:
                        tempSet.add("{}{}".format(str1, str2))
            result = tempSet
        return list(result)


class CycleDetectedException(Exception):
    pass


def flattenAlgorithmWithConditions(node: Node, conditions: Set = None, debug=True, recStack=None):
    if conditions is None:
        conditions = set()
    if recStack is None:
        recStack = list()

    # We keep nodes in current recursion stack in a set. If current node has been already added
    # to this list, it means we are expanding a node from upper levels which is a cycle.
    if node in recStack:
        print(f'Conditions:', conditions)
        for idx, item in enumerate(recStack):
            print(f'{idx}: {item.getValue()}')
        raise CycleDetectedException('We have a cycle here!!')

    recStack.append(node)
    # logging.debug("++++++ Flatten node with name: " + node.getName())

    flattedResult = None
    # We return result from memoize variable if available:
    if isinstance(node, LiteralNode):
        flattedResult = [(node.getValue(), conditions)]
    elif isinstance(node, TargetNode):
        flattedResult = [(node.rawName, conditions)]
    elif isinstance(node, OptionNode):
        # TODO: We may want to consider the default value for option
        flattedResult = []
    elif isinstance(node, RefNode):
        # If RefNode is a symbolic node, it may not have point to attribute
        if node.getPointTo() is None:
            flattedResult = [(node.rawName, conditions)]
            # flattedResult = []
        else:
            flattedResult = flattenAlgorithmWithConditions(node.getPointTo(), conditions,
                                                           debug, recStack)
    elif isinstance(node, CustomCommandNode):
        flattedResult = flattenCustomCommandNode(node, conditions, recStack)
        if flattedResult is None:
            flattedResult = []
    elif isinstance(node, SelectNode):
        flattedResult = []
        # Check if conditions satisfiable before expanding the tree (Using Z3)
        assertion = node.rule.getCondition().getAssertions()
        if node.trueNode:
            # Add facts about the variables in the condition expression
            for priorKnowledge in node.rule.flattenedResult:
                s = Solver()
                # Variables in the condition
                s.add(priorKnowledge)
                # Facts from the starting point to here
                s.add(conditions)
                if s.check() == unsat:
                    continue
                # As we simplify the assertions, there is a chance that the fact has been already added
                if assertion not in s.assertions():
                    s.add(assertion)
                if s.check() == sat:
                    flattedResult += flattenAlgorithmWithConditions(node.trueNode,
                                                                    set(s.assertions()),
                                                                    debug, recStack)
        if node.falseNode:
            for priorKnowledge in node.rule.flattenedResult:
                s = Solver()
                s.add(priorKnowledge)
                s.add(conditions)
                # Why did we not add this here?
                if s.check() == unsat:
                    continue
                falseAssertion = simplify(Not(assertion))
                if falseAssertion not in s.assertions():
                    s.add(falseAssertion)
                if s.check() == sat:
                    flattedResult += flattenAlgorithmWithConditions(node.falseNode,
                                                                    set(s.assertions()),
                                                                    debug, recStack)
    elif isinstance(node, ConcatNode):
        result = list()
        children = node.getChildren()
        
        for idx, item in enumerate(children):
            childSet = flattenAlgorithmWithConditions(item, conditions, debug, recStack)
            tempSet = list()
            # The flattened values for a child could be empty, skipping ...
            if not childSet:
                continue
            # Initially, the result should be equal of the first child that has a value
            if not result:
                result = list(childSet)
                continue

            # logging.debug('ConcatNode {}: Appending child {} {} of {} with {} childset'.format(
            #     node.getName(), item.getName(), idx + 1, numberOfChildren, len(childSet)
            # ))

            # There are two types of concat node. One which concat the literal string
            # and other one which make a list of values; Note that result and childSet are guaranteed to have values
            for str1 in result:
                for str2 in childSet:
                    # There shouldn't be any contradiction in the returned conditions.
                    s = Solver()
                    # We need to simplify the whole expressions
                    g = Goal()
                    g.add(str1[1])
                    g.add(str2[1])
                    s.add(g.simplify())

                    if s.check() == sat:
                        newConditions = set(s.assertions())
                        if node.concatString:
                            tempSet.append(("{}{}".format(str1[0], str2[0]), newConditions))
                        else:
                            if (str2[0], newConditions) not in tempSet:
                                tempSet.append((str2[0], newConditions))
                            if (str1[0], newConditions) not in tempSet:
                                tempSet.append((str1[0], newConditions))

                    if not node.concatString:
                        if (str2[0], str2[1]) not in tempSet:
                            tempSet.append((str2[0], str2[1]))
                        if (str1[0], str1[1]) not in tempSet:
                            tempSet.append((str1[0], str1[1]))

            result = list(tempSet)
        flattedResult = result if result != [''] else []
    recStack.remove(node)
    return flattedResult


def flattenCustomCommandNode(node: CustomCommandNode, conditions: Set, recStack, lookup=None):
    # print("##### Start evaluating custom command " + node.rawName)
    if conditions is None:
        conditions = set()
    result = None
    if 'file' in node.getName().lower():
        arguments = node.commands[0].getChildren()
        fileCommandType = arguments[0].getValue()
        if fileCommandType.upper() == 'GLOB':
            arguments = flattenAlgorithmWithConditions(node.commands[0].getChildren()[1],
                                                       conditions, recStack=recStack)
            result = []
            for arg in arguments:
                wildcardPath = re.findall('"(.*)"', arg[0])
                if wildcardPath:
                    wildcardPath = wildcardPath[0]
                else:
                    wildcardPath = arg[0]
                for item in glob.glob(os.path.join(node.extraInfo.get('pwd'), wildcardPath)):
                    result.append([item, arg[1]])
            return result
    elif 'target_link_libraries' in node.rawName.lower():
        result = []
        arguments = node.commands[0].getChildren()[1:]
        for argument in arguments:
            flattenedFiles = flattenAlgorithmWithConditions(argument, conditions, recStack=recStack)
            finalFlattenList = []
            for item in flattenedFiles:
                if isinstance(item[0], Node):
                    # logging.debug('target_link_libraries: calling recursivelyResolveReference to' \
                    #               'resolve node with name: {}'.format(item[0].getName()))
                    finalFlattenList += recursivelyResolveReference(item[0], item[1])
                else:
                    finalFlattenList.append(item)
            for item in finalFlattenList:
                node = VModel.getInstance().lookupTable.getKey("t:{}".format(item[0]))
                if isinstance(node, TargetNode):
                    result += flattenAlgorithmWithConditions(node.sources, item[1], recStack=recStack)
                    if node.linkLibraries:
                        result += flattenAlgorithmWithConditions(node.linkLibraries, item[1], recStack=recStack)
                    # for library, conditions in node.linkLibrariesConditions.items():
                    #     s = Solver()
                    #     # We need to simplify the whole expressions
                    #     g = Goal()
                    #     g.add(conditions)
                    #     g.add(item[1])
                    #     s.add(g.simplify())
                    #     if s.check() == sat:
                    #         result += flattenAlgorithmWithConditions(library, set(s.assertions()),
                    #                                                  recStack=recStack)
    elif 'remove_item' in node.getName().lower():
        arguments = flattenAlgorithmWithConditions(node.commands[0], conditions, recStack=recStack)
        result = flattenAlgorithmWithConditions(node.depends[0], conditions, recStack=recStack)
        for argument in arguments:
            for item in result:
                if item[0] == argument[0]:
                    result = [i for i in result if i != item]

    elif 'remove_at' in node.getName().lower():
        arguments = node.commands[0].getChildren()
        result = flattenAlgorithmWithConditions(node.depends[0], conditions, recStack=recStack)
        for argument in arguments:
            del result[argument.getValue()]
 
    elif 'directory_definitions' in node.getName().lower():
        # Normally, there are 2 dependents for each definition node: 'directory_definition_(i+1) and a 
        # definition command like add_definition. Sometimes, we also have to concat
        # Also, the ordering here is important because index 0 is the command, index 1 is 
        # the directory_definitions_(i+1)
        result = []
        for dependent in node.depends:
            result += flattenAlgorithmWithConditions(dependent, conditions, recStack=recStack)
    
    elif 'target_definitions' in node.getName().lower():
        result = []
        result += flattenCustomCommandNode(node.commands[0], conditions, recStack=recStack)
        if node.depends:
            result += flattenAlgorithmWithConditions(node.depends[0], conditions, recStack=recStack)
        return result

    elif 'target_definitions' in node.getName().lower():
        # Similar to the directory_definitions
        result = []
        for dependent in node.depends:
            result += flattenAlgorithmWithConditions(dependent, conditions, recStack=recStack)

    elif 'target_compile_definitions' in node.getName().lower():
        result = flattenAlgorithmWithConditions(node.commands[0], conditions, recStack=recStack)

    elif 'add_definitions' in node.getName().lower():
        global directory_definition_stack
        # There is only one parent for each CommandDefinitionNode,
        # and it has the ordering value within
        ordering = node.parent[0].ordering 
        result = flattenAlgorithmWithConditions(node.commands[0], conditions, recStack=recStack)
        flags_to_add = [flag[0] for flag in result]
        for flag in flags_to_add:
            directory_definition_stack[flag] = ordering

    elif 'remove_definitions' in node.getName().lower():
        temp_result = flattenAlgorithmWithConditions(node.commands[0], conditions, recStack=recStack)
        result = []
        for e in temp_result:
            flag, condition = e[0], e[1]
            if flag not in directory_definition_stack:
                # Since the flags have not been introduced by add_definitions, 
                # there is nothing we need to do
                logging.info(f"REMOVE: flags {flag} not yet added")
                continue
            else:
                # take the negation of all of the nodes' condition
                if len(condition) == 0:
                    new_condition = {False}
                elif len(condition) == 1:
                    new_condition = {Not(*condition)}
                else:
                    new_condition = {Not(And(*condition))}
            result.append((flag, new_condition))
    return result


# Flatten Definition requires a very convoluted traversal ordering that requires parent's 
# information recursively, so we cannot just recurse normally
def getFlattenedDefinitionsFromNode(node: Node, conditions: Set = None, debug=True, recStack=None):
    # There are only type of nodes following a definition edge.
    children = node.getChildren()
    directory_node, target_node = None, None
    if len(children) == 1:
        if children[0].from_dir:
            directory_node = children[0]
        else:
            target_node = children[0]
    elif len(children) == 2:
        if children[0].from_dir:
            directory_node = children[0]
            target_node = children[1]
        else:
            target_node = children[0]
            directory_node = children[1]
    dir_result = flattenDirectoryDefinitions(directory_node, conditions, recStack)
    target_result = flattenTargetDefinitions(target_node, conditions, recStack)
    # Now this gives us all the flattened result for the directory side,
    # we have to reconcile the data with the target side.
    result = mergeDirectoryAndTargetDefinitions(dir_result, target_result)
    return result


def find_name(to_find, name):
    res = []
    for idx, t in enumerate(to_find):
        if t[0] == name:
            res.append(idx)
    return res


def mergeFlattenedDefinitionResults(global_result, local_result, command_type):
    # Can clearly be optimized with the use of a dictionary, but I don't think the scale requires it
    to_add = True if command_type == 'add' else False
    result = global_result
    for r in local_result:
        name, cond = r
        indices = find_name(global_result, name)
        if indices:
            for idx in indices:
                g_name, g_cond = global_result[idx]
                g_cond = {And(*g_cond)} if len(g_cond) > 1 else g_cond
                cond = {And(*cond)} if len(cond) > 1 else cond
                if to_add:
                    result[idx] = (g_name, {Or(*g_cond, *cond)})
                else:
                    result[idx] = (g_name, {And(*g_cond, *cond)})
        else:
            result.append((name, cond))
    return result


def mergeDirectoryAndTargetDefinitions(directory_result, target_result):
    # something need to be fixed here
    result = directory_result 
    for tar in target_result:
        flag, cond = tar
        indices = find_name(result, flag)
        if not indices:
            result.append((flag, cond))
            continue
        for idx in indices:
            r_flag, r_cond = result[idx]
            result[idx] = (r_flag, {Or(*r_cond, *cond)})
    return result


def flattenTargetDefinitions(node: CustomCommandNode, conditions: Set, recStack, lookup=None):
    if node is None:
        return []
    result = flattenCustomCommandNode(node, conditions, recStack, lookup)
    return result


def flattenDirectoryDefinitions(node: CustomCommandNode, conditions: Set, recStack, lookup=None):
    if node is None:
        return []
    result = []
    # first recurse through all its inheritance
    # currently we only inherit from one parent, and I don't think this will 
    # change in the forseeable future.
    cur_node = node
    inheritance_path = [cur_node]
    while cur_node.inherits:
        cur_node = cur_node.inherits[0]
        inheritance_path.append(cur_node)
    # Now, we recurse down from the parent until the end of the current directory.
    # we can now use _reverse_inherits here until we reach node
    cur_root_node = inheritance_path.pop()
    while inheritance_path:
        if cur_node.commands:
            # When the definition node is not added in retrospect to fit in with the architecture
            # where there is actually directory-based definition defined for this specific directory
            cur_command = cur_node.commands[0] # This is a custom command like add_definitions/remove_definitions
            cur_result = flattenCustomCommandNode(cur_command, conditions, recStack)
            result = mergeFlattenedDefinitionResults(result, cur_result, cur_command.command_type)

        if not cur_node.depends:
            if inheritance_path:
                # jump to the next subdirectory
                cur_root_node = inheritance_path.pop()        
                cur_node = cur_root_node
            else:
                cur_root_node = None
                continue
        else:
            next_node = cur_node.depends[0]
            assert isinstance(next_node, DefinitionNode)
            if next_node.ordering > cur_node.ordering + 1:
                # jump to the subdirectory
                cur_root_node = inheritance_path.pop()
                cur_node = cur_root_node
            else:
                # first work on the commands side
                # then, we simply traverse to the next dependent
                cur_node = cur_node.depends[0]        
    # if this is the last node in the inheritance path, just loop through dependents, because 
    # there you are in the lowest level and no longer have to go down the stack.
    while cur_node:
        if not cur_node.commands:
            break
        cur_command = cur_node.commands[0] # This is a custom command like add_definitions/remove_definitions
        cur_result = flattenCustomCommandNode(cur_command, conditions, recStack)
        if not cur_node.depends:
            cur_node = None
        else:
            cur_node = cur_node.depends[0]
        result = mergeFlattenedDefinitionResults(result, cur_result, cur_command.command_type)
    return result


# Given a Node (often a ConcatNode) this algorithm will return flatted arguments
def getFlattedArguments(argNode: Node):
    result = []
    if isinstance(argNode, LiteralNode):
        return [argNode.getValue()]
    for arg in argNode.getChildren():
        result.append("".join(flattenAlgorithm(arg)))
    return result


def recursivelyResolveReference(item, conditionToAppend):
    logging.debug('Recursively resolve node with name: {}'.format(item.getName()))
    result = []
    for x, y in VModel.getInstance().flattenMemoize[item]:
        if isinstance(x, Node):
            tempResult = recursivelyResolveReference(x, set(y).union(conditionToAppend))
            result += tempResult
        else:
            result.append((x, set(y).union(conditionToAppend)))

    return result


def mergeFlattedList(flatted: List) -> Dict:
    print("Start merging the flatted list")
    result = defaultdict(list)
    for item in flatted:
        condition_key = frozenset(item[1])
        result[condition_key].append(item[0])
    return result


# Remove items with the same value, different conditions, but one of the conditions is a subset of another one
def removeDuplicatesFromFlattedList(flatted: Dict) -> List:
    print("Start removing duplicates the flatted list")
    result = []
    for flatted_item in flatted.keys():
        found = False
        for result_index in range(len(result)):
            result_item = result[result_index]
            if result_item[0] == flatted.get(flatted_item):
                if flatted_item.issubset(result_item[1]):
                    found = True
                    result.pop(result_index)
                    result.insert(result_index, (flatted.get(flatted_item), flatted_item))
                elif result_item[1].issubset(flatted_item):
                    found = True
        if found is False:
            result.append((flatted.get(flatted_item), flatted_item))
    return result


# This function will run simplifier on the facts and cast them to string
def postprocessZ3Output(flattened: List):
    for idx, item in enumerate(flattened):
        g = Goal()
        t = Tactic('ctx-solver-simplify')
        g.add(item[1])
        flattened[idx] = (item[0], t(g)[0])
