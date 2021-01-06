import glob
import logging
import os
import re
from collections import Set

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


def flattenAlgorithmWithConditions(node: Node, conditions: Set = None, debug=True, recStack=None, useCache=True):
    if conditions is None:
        conditions = set()
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
    if useCache and node in VModel.getInstance().flattenMemoize:
        logging.debug("CACHE HIT for " + node.getName())
        flattedResult = [(x, set(y)) for x, y in VModel.getInstance().flattenMemoize[node]]
        # flattedResult = [(node, conditions)]
    elif isinstance(node, LiteralNode):
        flattedResult = [(node.getValue(), conditions)]
    elif isinstance(node, TargetNode):
        flattedResult = [(node.rawName, conditions)]
    elif isinstance(node, RefNode):
        # If RefNode is a symbolic node, it may not have point to attribute
        if node.getPointTo() is None:
            flattedResult = [(node.rawName, conditions)]
        else:
            flattedResult = flattenAlgorithmWithConditions(node.getPointTo(), None, debug, recStack, useCache=useCache)
    elif isinstance(node, CustomCommandNode):
        flattedResult = flattenCustomCommandNode(node, None, recStack)
    elif isinstance(node, SelectNode):
        # TODO: Check if conditions satisfiable before expanding the tree (Using the new data structure)
        if node.falseNode and node.trueNode:
            flattedResult = flattenAlgorithmWithConditions(node.falseNode, {(node.args, False)}, debug, recStack,
                                                           useCache=useCache) + \
                            flattenAlgorithmWithConditions(node.trueNode, {(node.args, True)}, debug, recStack,
                                                           useCache=useCache)
        elif node.trueNode:
            flattedResult = flattenAlgorithmWithConditions(node.trueNode, {(node.args, True)}, debug, recStack,
                                                           useCache=useCache)
        elif node.falseNode:
            flattedResult = flattenAlgorithmWithConditions(node.falseNode, {(node.args, False)}, debug, recStack,
                                                           useCache=useCache)
    elif isinstance(node, ConcatNode):
        result = ['']
        numberOfChildren = len(node.getChildren())
        for idx, item in enumerate(node.getChildren()):
            childSet = flattenAlgorithmWithConditions(item, None, debug, recStack, useCache=useCache)
            tempSet = []
            if childSet is None:
                continue

            logging.debug('ConcatNode {}: Appending child {} {} of {} with {} childset'.format(
                node.getName(), item.getName(), idx + 1, numberOfChildren, len(childSet)
            ))

            # There are two types of concat node. One which concat the literal string
            # and other one which make a list of values
            if node.concatString:
                for str1 in result:
                    # Now we should expand the cached results
                    finalFlattenList = []
                    for subItem in childSet:
                        if isinstance(subItem[0], Node):
                            finalFlattenList += recursivelyResolveReference(subItem[0], subItem[1])
                        else:
                            finalFlattenList.append(subItem)
                    for str2 in finalFlattenList:
                        if str1 == '':

                            tempSet.append(str2)
                        else:
                            tempSet.append(["{}{}".format(str1[0], str2[0]), str1[1].union(str2[1])])
                result = tempSet
            else:
                if result[0] == '':
                    result = childSet
                else:
                    result += childSet
        flattedResult = result

    if useCache and node not in VModel.getInstance().flattenMemoize and flattedResult:
        copied_result = [(x, set(y)) for x, y in flattedResult]
        VModel.getInstance().flattenMemoize[node] = copied_result

    recStack.remove(node)

    if conditions and flattedResult:
        for item in flattedResult:
            item[1].update(conditions)

    # Try to remove items with condition both false and true
    if flattedResult:
        for row in list(flattedResult):
            for condition in row[1]:
                if (condition[0], not condition[1]) in row[1]:
                    flattedResult.remove(row)
                    break
    return flattedResult


def flattenCustomCommandNode(node: CustomCommandNode, conditions, recStack, lookup=None):
    print("##### Start evaluating custom command " + node.rawName)
    if conditions is None:
        conditions = set()

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

