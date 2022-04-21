# Convert list of strings to a string separated by space.
from typing import List, Optional
from z3 import And

from data_model.condition_data_structure import LogicalExpression, NotExpression, AndExpression, Rule, ConstantExpression, \
    DummyExpression
from data_model.datastructs import SelectNode, Node, RefNode, Lookup
from data_model.vmodel import VModel


def util_getStringFromList(lst: List):
    return " ".join(lst)


# Given a list of strings, the function will return the next item after a given string name
def util_extract_variable_name(argName: str, arguments: List) -> Optional[str]:
    if argName in arguments:
        argIndex = arguments.index(argName)
        arguments.pop(argIndex)
        return arguments.pop(argIndex)
    return None


def util_create_and_add_refNode_for_variable(varName: str, nextNode: Node,
                                             parentScope=False, relatedProperty=None) -> RefNode:
    vmodel = VModel.getInstance()
    lookupTable = Lookup.getInstance()
    variable_name = "${{{}}}".format(varName)
    # Each variable has its own RefNode
    variableNode = RefNode("{}".format(variable_name), nextNode)
    if relatedProperty:
        variableNode.relatedProperty = relatedProperty

    variableNode.pointTo = util_handleConditions(nextNode, variable_name)

    # Finally, we add the new RefNode to the graph and our lookup table
    vmodel.nodes.append(variableNode)
    lookupTable.setKey(variable_name, variableNode, parentScope)
    return variableNode


# This function looks for previously defined node in the lookup table which works for variables and targets, but
# not for other nodes that we don't push to lookup table. This third argument helps to manually pass that node.
def util_handleConditions(nextNode, newNodeName, prevNode=None, prior_condition=None):
    vmodel = VModel.getInstance()
    # If inside condition, we just create a SelectNode after newly created RefNode (Node)
    # which true edge points to the new node created for the arguments.
    # If the variable were already defined before the if, the false edge points to that
    systemState = None
    stateProperty = None

    # There could be a prior condition apply to the node, for example, a target node that target name is depend
    # on another condition, and the target node itself is inside a if condition. The prior knowledge is for the
    # conditions applied on the name
    if prior_condition:
        logicalExpression = DummyExpression(prior_condition)
        selectNodeName = "SELECT_{}_{}".format(newNodeName,
                                               str(prior_condition))
        newSelectNode = SelectNode(selectNodeName, '')
        newSelectNode.rule = Rule()
        newSelectNode.rule.setCondition(logicalExpression)
        newSelectNode.setTrueNode(nextNode)
        nextNode = newSelectNode

    # The for statement will traverse all nested if nodes and create corresponding select node for each of them
    # However, we only interested in states in outer levels. So, we skip the ones in a same level
    # For example, in an if -> if | else scenario, when we are processing the else, we skip in inner most if
    currentIfLevel = 1000
    for systemStateObject in reversed(vmodel.systemState):
        level = systemStateObject.level
        systemState = systemStateObject.type
        stateProperty = systemStateObject.args
        if systemState in ('while', 'foreach'):
            continue
        if currentIfLevel == level:
            continue
        currentIfLevel = min(currentIfLevel, level)
        if systemState == 'if' or systemState == 'else' or systemState == 'elseif':
            selectNodeName = "SELECT_{}_{}".format(newNodeName,
                                                   util_getStringFromList(stateProperty))
            newSelectNode = SelectNode(selectNodeName, stateProperty)
            newSelectNode.args = vmodel.expand(stateProperty)
            newSelectNode.rule = systemStateObject

            if systemState == 'if' or systemState == 'elseif':
                newSelectNode.setTrueNode(nextNode)
            elif systemState == 'else':
                newSelectNode.setFalseNode(nextNode)
            # Inside if statement, we set true node to the variable defined outside if which pushed
            # to this stack before entering the if statement
            if prevNode or vmodel.getLastPushedLookupTable().getKey(newNodeName):
                if systemState == 'if' or systemState == 'elseif':
                    newSelectNode.setFalseNode(prevNode or vmodel.getLastPushedLookupTable().getKey(newNodeName))
                elif systemState == 'else':
                    newSelectNode.setTrueNode(prevNode or vmodel.getLastPushedLookupTable().getKey(newNodeName))
            nextNode = newSelectNode
            # newNodeName = nextNode.name

    return nextNode


def util_getNegativeOfPrevLogics():
    vmodel = VModel.getInstance()
    # Previous expression could be an if or elseif. So, there are two cases that we have to handle:
    # 1. If: We should "not" the condition and "and" it with the elseif condition
    # 2. elseif: We already calculated not of the previous ones in the leftSide, so we only need to not the
    # rightSide and and it with the current one.
    prevState = vmodel.systemState[-1]
    logic: LogicalExpression
    if prevState.getType() == 'if':
        logic = NotExpression(prevState.getCondition())
    elif prevState.getType() == 'elseif':
        logic = AndExpression(prevState.getCondition().getLeft(),
                              NotExpression(prevState.getCondition().getRight()))
    else:
        raise RuntimeError("Previous state of elseif could be if or elseif, but got {}".format(prevState.getType()))
    return logic, prevState.flattenedResult


def util_preprocess_definition_names(names, force=False):
    results = []
    if force:
        # this is for the usecase of target_compile_definition, 
        # where definitions are added without specifying -D
        results = [f"-D{name}" for name in names]
    else:
        results = list(map(lambda x: f"-D{x[2:]}" if x[0:2] == '/D' else x, names))
    return results