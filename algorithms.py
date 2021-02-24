import glob
import logging
import os
import re
from collections import Set
from typing import Dict, List

from datastructs import Node, LiteralNode, RefNode, CustomCommandNode, SelectNode, ConcatNode, TargetNode
from vmodel import VModel


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


def flattenAlgorithmWithConditions(node: Node, conditions: Dict = None, debug=True, recStack=None, useCache=True):
    if conditions is None:
        conditions = dict()
    if recStack is None:
        recStack = list()

    # We keep nodes in current recursion stack in a set. If current node has been already added
    # to this list, it means we are expanding a node from upper levels which is a cycle.
    if node in recStack:
        raise Exception('We have a cycle here!!')

    recStack.append(node)
    logging.debug("++++++ Flatten node with name: " + node.getName())

    flattedResult = None
    # We return result from memoize variable if available:
    if isinstance(node, LiteralNode):
        flattedResult = [(node.getValue(), conditions)]
    elif isinstance(node, TargetNode):
        flattedResult = [(node.rawName, conditions)]
    elif isinstance(node, RefNode):
        # If RefNode is a symbolic node, it may not have point to attribute
        if node.getPointTo() is None:
            flattedResult = [(node.rawName, conditions)]
        else:
            flattedResult = flattenAlgorithmWithConditions(node.getPointTo(), conditions,
                                                           debug, recStack, useCache=useCache)
    elif isinstance(node, CustomCommandNode):
        flattedResult = flattenCustomCommandNode(node, conditions, recStack)
    elif isinstance(node, SelectNode):
        # Check if conditions satisfiable before expanding the tree (Using the new data structure)
        possible_evaluation = node.rule.getCondition().satisfiable(conditions)
        true_evaluations = [evaluation for evaluation in possible_evaluation if evaluation[0]]
        false_evaluations = [evaluation for evaluation in possible_evaluation if evaluation[0] is False]
        flattedResult = []
        if node.falseNode and false_evaluations:
            for evaluation in false_evaluations:
                flattedResult += flattenAlgorithmWithConditions(node.falseNode,
                                                                {**conditions, **evaluation[1]},
                                                                debug, recStack, useCache=useCache)
        if node.trueNode and true_evaluations:
            for evaluation in true_evaluations:
                flattedResult += flattenAlgorithmWithConditions(node.trueNode,
                                                                {**conditions, **evaluation[1]},
                                                                debug, recStack, useCache=useCache)
    elif isinstance(node, ConcatNode):
        result = ['']
        numberOfChildren = len(node.getChildren())
        for idx, item in enumerate(node.getChildren()):
            childSet = flattenAlgorithmWithConditions(item, conditions, debug, recStack, useCache=useCache)
            tempSet = []
            if childSet is None:
                continue

            logging.debug('ConcatNode {}: Appending child {} {} of {} with {} childset'.format(
                node.getName(), item.getName(), idx + 1, numberOfChildren, len(childSet)
            ))

            # There are two types of concat node. One which concat the literal string
            # and other one which make a list of values
            for str1 in result:
                for str2 in childSet:
                    if str1 == '':
                        tempSet.append(str2)
                    else:
                        # There shouldn't be any contradiction in the returned conditions. If there is, we won't
                        # append the value to the one with contradiction
                        contradiction = False
                        for common_key in set(str1[1]).intersection(set(str2[1])):
                            if str1[1].get(common_key) != str2[1].get(common_key):
                                contradiction = True
                        if contradiction:
                            continue
                        if node.concatString:
                            tempSet.append(("{}{}".format(str1[0], str2[0]), {**str1[1], **str2[1]}))
                        elif (str2[0], {**str1[1], **str2[1]}) not in tempSet:
                            tempSet.append((str1[0], {**str1[1], **str2[1]}))
                            tempSet.append((str2[0], {**str1[1], **str2[1]}))
            result = tempSet
        flattedResult = result
    recStack.remove(node)
    return flattedResult


def flattenCustomCommandNode(node: CustomCommandNode, conditions, recStack, lookup=None):
    print("##### Start evaluating custom command " + node.rawName)
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
                    logging.debug('target_link_libraries: calling recursivelyResolveReference to' \
                                  'resolve node with name: {}'.format(item[0].getName()))
                    finalFlattenList += recursivelyResolveReference(item[0], item[1])
                else:
                    finalFlattenList.append(item)
            for item in finalFlattenList:
                node = VModel.getInstance().lookupTable.getKey("t:{}".format(item[0]))
                if isinstance(node, TargetNode):
                    result += flattenAlgorithmWithConditions(node.sources, item[1], recStack=recStack)
                    for library, conditions in node.linkLibrariesConditions.items():
                        result += flattenAlgorithmWithConditions(library, conditions.union(item[1]),
                                                                 recStack=recStack)
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


def mergeFlattedList(flatted: List) -> List:
    result = []
    for item in flatted:
        found = False
        for result_item in result:
            if result_item[1] == item[1]:
                result_item[0].add(item[0])
                found = True
        if found is False:
            result.append((set([item[0]]), item[1]))
    return result


def removeDuplicatesFromFlattedList(flatted: List) -> List:
    result = []
    for flatted_item in flatted:
        found = False
        for result_index in range(len(result)):
            result_item = result[result_index]
            if result_item[0] == flatted_item[0] and all(item in result_item[1].items() for item in flatted_item[1].items()):
                found = True
                result.pop(result_index)
                result.insert(result_index, flatted_item)
            elif result_item[0] == flatted_item[0] and all(item in flatted_item[1].items() for item in result_item[1].items()):
                found = True
        if found is False:
            result.append(flatted_item)
    return result
