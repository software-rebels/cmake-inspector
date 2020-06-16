from enum import Enum, auto
from typing import Optional, List, Set, Dict
from graphviz import Digraph
import copy
from datalayer import Target, Reference, Concat, Literal, Select
import re

VARIABLE_REGEX = r"\${(\S*)}"


def infinite_sequence():
    num = 0
    while True:
        yield num
        num += 1


# class NodeType(Enum):
#     TARGET = auto()
#
#
# class Node:
#     def __init__(self, type: NodeType, dataval=None):
#         self.type = type
#         self.dataval = dataval
#
#
# class Flow:
#     def __init__(self):
#         self.variables = {}
#         self.relations: List[Flow] = []
#
#
# class FlowRelation:
#     _instance = None
#
#     def __init__(self, flow: Flow):
#         self.flows: List[Flow] = [Flow()]
#
#     @classmethod
#     def getInstance(cls):
#         if cls._instance is None:
#             cls._instance = FlowRelation(Flow())
#         return cls._instance


class Node:
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.parent: List[Optional[Node]] = []
        self.isVisited = False
        self.dbNode = None

    def getName(self):
        return self.name

    def getNodeName(self):
        return self.getName()

    def getChildren(self) -> Optional[List]:
        return []

    def getNeighbours(self):
        if self.getChildren():
            return self.getChildren() + self.parent
        return self.parent

    def addParent(self, node: "Node"):
        self.parent.append(node)

    def getValue(self):
        return None

    def __hash__(self):
        return hash(self.name)


class TargetNode(Node):
    def __init__(self, name: str, pointTo: Node):
        super().__init__(name)
        self.pointTo = pointTo
        self.definitions = None
        self.linkLibraries = None
        self.scope = None

    def getPointTo(self) -> Node:
        return self.pointTo

    def getChildren(self):
        result = [self.pointTo]
        if self.definitions:
            result.append(self.definitions)
        if self.linkLibraries:
            result.append(self.linkLibraries)
        return result

    def setDefinition(self, node: Node):
        self.definitions = node

    def getDefinition(self):
        return self.definitions


class TestNode(Node):
    def __init__(self, name: str, pointTo: Node):
        super().__init__(name)
        self.pointTo = pointTo

    def getPointTo(self) -> Node:
        return self.pointTo

    def getChildren(self):
        return [self.pointTo]


class RefNode(Node):
    def __init__(self, name: str, pointTo: Optional[Node]):
        super().__init__(name)
        self.pointTo = pointTo

    def getPointTo(self) -> Node:
        return self.pointTo

    def getChildren(self):
        if self.pointTo:
            return [self.pointTo]
        return None

    def getTerminalNodes(self):
        result = []
        toExplore = self.getChildren()
        while toExplore:
            child = toExplore.pop(0)
            if isinstance(child, LiteralNode):
                result.append(child)
            elif child.getChildren():
                toExplore += child.getChildren()
            else:
                result.append(child)
        return result

    def getValue(self):
        return self.pointTo.getName()


class CustomCommandNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.pointTo: List[Node] = []

    def getChildren(self) -> Optional[List]:
        if self.pointTo:
            return self.pointTo
        return None


class ConcatNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.listOfNodes = list()

    def getNodeName(self):
        return "CONCAT"

    def addNode(self, node: Node):
        self.listOfNodes.append(node)

    def addToBeginning(self, node: Node):
        self.listOfNodes.insert(0, node)

    def getNodes(self) -> List[Node]:
        return self.listOfNodes

    def getChildren(self):
        return self.getNodes()


class LiteralNode(Node):
    def __init__(self, name, value=""):
        super().__init__(name)
        self.value = value

    def setValue(self, value):
        self.value = value

    def getValue(self):
        return self.value


class SelectNode(Node):
    def __init__(self, name, condition):
        super().__init__(name)
        self.trueNode: Optional[Node] = None
        self.falseNode: Optional[Node] = None
        self.conditionList = copy.deepcopy(condition)
        self.condition = " ".join(condition)

    def getNodeName(self):
        return "SELECT\n" + self.condition

    def setTrueNode(self, node: Node):
        self.trueNode = node

    def setFalseNode(self, node: Node):
        self.falseNode = node

    def getChildren(self):
        result = list()
        if self.trueNode:
            result.append(self.trueNode)
        if self.falseNode:
            result.append(self.falseNode)
        return result


class Lookup:
    _instance = None

    def __init__(self):
        self.items = [{}]
        self.variableHistory = {}

    def newScope(self):
        self.items.append({})

    def setKey(self, key, value, parentScope=False):
        if key not in self.variableHistory:
            self.variableHistory[key] = []

        self.variableHistory[key].append(value)
        if parentScope:
            self.items[-2][key] = value
        else:
            self.items[-1][key] = value

    def getKey(self, key) -> Optional[RefNode]:
        for table in reversed(self.items):
            if key in table:
                return table.get(key)
            return None

    def getVariableHistory(self, key) -> List[RefNode]:
        return self.variableHistory[key]

    def deleteKey(self, key, parentScope=False):
        if parentScope:
            del (self.items[-2][key])
        else:
            del (self.items[-1][key])

    def dropScope(self):
        self.items.pop()

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.items = []
        for item in self.items:
            result.items.append(dict.copy(item))
        return result

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = Lookup()

        return cls._instance

    @classmethod
    def clearInstance(cls):
        cls._instance = None


def flattenAlgorithm(node: Node):
    if isinstance(node, LiteralNode):
        return [node.getValue()]
    elif isinstance(node, RefNode):
        return flattenAlgorithm(node.getPointTo())
    elif isinstance(node, SelectNode):
        return flattenAlgorithm(node.falseNode) + flattenAlgorithm(node.trueNode)
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
                        tempSet.add("{} {}".format(str1, str2))
            result = tempSet
        return list(result)


class VModel:
    _instance = None

    def __init__(self):
        self.nodes: Optional[List[Node]] = []
        self.ifLevel = 0
        self.ifConditions = []
        self.targets = set()
        self.testTargets = set()
        self.options = dict()
        self.lookupTable = Lookup.getInstance()
        self.recordCommands = False
        self.COUNTER = infinite_sequence()
        self.tmpLookupTableStack = []
        self.systemState = []
        self.functions = {}
        self.currentFunctionCommand = None

    def pushSystemState(self, state, properties):
        self.systemState.append((state, properties))

    def getCurrentSystemState(self):
        if self.systemState:
            return self.systemState[-1]
        else:
            return None

    def popSystemState(self):
        return self.systemState.pop()

    def pushCurrentLookupTable(self):
        newLookup = copy.copy(self.lookupTable)
        self.tmpLookupTableStack.append(newLookup)

    def getLastPushedLookupTable(self) -> Lookup:
        return self.tmpLookupTableStack[-1]

    def popLookupTable(self):
        return self.tmpLookupTableStack.pop()

    def getNextCounter(self):
        return str(next(self.COUNTER))

    def addOption(self, optionName, initialValue):
        self.options[optionName] = initialValue

    def enableRecordCommands(self):
        self.recordCommands = True

    def disableRecordCommands(self):
        self.recordCommands = False

    def shouldRecordCommand(self):
        return self.recordCommands

    def setInsideIf(self):
        self.ifLevel += 1

    def setOutsideIf(self):
        self.ifLevel -= 1

    def isInsideIf(self):
        return self.ifLevel > 0

    def setParents(self):
        result = set()
        # result.add(node)
        nodesToVisit = []
        for node in self.nodes:
            nodesToVisit.append(node)

        while nodesToVisit:
            node = nodesToVisit.pop()
            if node in result:
                continue
            result.add(node)
            if node.getChildren() is not None:
                for child in node.getChildren():
                    child.addParent(node)
                nodesToVisit += node.getChildren()

    def getNodesCluster(self):
        self.setParents()
        nodeSet = self.getNodeSet()
        clusters = []
        for node in nodeSet:
            if node.isVisited:
                continue
            newCluster = []
            nodeToVisit = [node]
            while nodeToVisit:
                node = nodeToVisit.pop()
                if node in newCluster:
                    continue
                node.isVisited = True
                newCluster.append(node)
                nodeToVisit += node.getNeighbours()
            clusters.append(newCluster)
        return clusters

    def getNodeSet(self) -> Set[Node]:
        nodesToVisit = []

        for node in self.nodes:
            nodesToVisit.append(node)

        nodes = set()
        while nodesToVisit:
            node = nodesToVisit.pop()
            if node in nodes:
                continue
            nodes.add(node)
            if node.getChildren() is not None:
                nodesToVisit += node.getChildren()
                # nodes.update(node.getChildren())
        return nodes

    @staticmethod
    def getNodeChildren(node: Node) -> Set[Node]:
        nodesToVisit = [node]
        result = set()
        while nodesToVisit:
            node = nodesToVisit.pop()
            if node in result:
                continue
            result.add(node)
            if node.getChildren() is not None:
                nodesToVisit += node.getChildren()
        return result

    def findNode(self, name: str):
        for node in self.getNodeSet():
            if node.getName() == name:
                return node
        return None

    # Iterate over a list of arguments, if it's a variable, we return the corresponding RefNode
    # Otherwise we return or create a literal node for that
    def flatten(self, textToFlat: List[str]) -> List[Node]:
        result = []
        processedText = []
        for item in textToFlat:
            tempText = re.split("(\${[A-Za-z_][A-Za-z0-9_]*})", item)
            for t in tempText:
                if t != "":
                    processedText.append(t)
        for item in processedText:
            variableName = re.findall(VARIABLE_REGEX, item)
            if variableName:
                node = self.lookupTable.getKey("${{{}}}".format(variableName[0]))
                if not isinstance(node, RefNode):
                    raise Exception("NOT_IMPLEMENTED")
                result.append(node)
            else:
                literalNode = self.findNode(item)
                if literalNode and not isinstance(literalNode, LiteralNode):
                    raise Exception("SHOULD_NOT_HAPPEN")
                elif not literalNode:
                    literalNode = LiteralNode(item, item)
                result.append(literalNode)
        return result

    def addNode(self, node: Node):
        previousNode = self.findNode(node.getName())
        if self.isInsideIf():
            selectNodeName = "SELECT_{}_{}".format(node.getName(), " ".join(self.ifConditions))
            if self.findNode(selectNodeName):
                raise Exception("DUPLICATE_SELECT_NODE_FOUND!")

            newSelectNode = SelectNode(selectNodeName, self.ifConditions)
            if isinstance(node, RefNode):
                newSelectNode.setTrueNode(node.getPointTo())
                if previousNode:
                    if not isinstance(previousNode, RefNode):
                        raise Exception("PREVIOUS NODE OF AN REF NODE SHOULD ALSO BE REF!")
                    newSelectNode.setFalseNode(previousNode.getPointTo())
                    previousNode.pointTo = newSelectNode
                    return
                else:
                    node.pointTo = newSelectNode
                    self.nodes.append(node)
                    return
            elif isinstance(node, TargetNode) or isinstance(node, TestNode):
                newSelectNode.setTrueNode(node.pointTo)
                node.pointTo = newSelectNode
                self.nodes.append(node)
                return

            else:
                raise Exception("NOT SUPPORTED YET!")

        if previousNode and not self.isInsideIf():
            raise Exception("NOT IMPLEMENTED YET!")

        self.nodes.append(node)

        # if previousNode:
        #     if isinstance(node, RefNode) and isinstance(previousNode, RefNode):
        #         self.nodes.remove(previousNode)
        #         newSelectNode = SelectNode("SELECT_" + previousNode.getName(), self.ifConditions)
        #         newSelectNode.setTrueNode(node.getPointTo())
        #         newSelectNode.setFalseNode(previousNode.getPointTo())
        #         newNode = RefNode(previousNode.getName(), newSelectNode)
        #         self.nodes.append(newNode)
        #         return
        #
        #     if not self.isInsideIf():
        #         raise Exception("NOT IMPLEMENTED YET!")
        #
        # else:
        #     if self.isInsideIf():
        #         if not isinstance(node, RefNode):
        #             self.nodes.append(node)
        #             return
        #
        #         newSelectNode = SelectNode("SELECT_" + node.getName(), self.ifConditions)
        #         newSelectNode.setTrueNode(node.getPointTo())
        #         newNode = RefNode(node.getName(), newSelectNode)
        #         self.nodes.append(newNode)
        #         return
        #
        #     self.nodes.append(node)

    def expand(self, expression: List[str]) -> Node:
        # A recursive function which retrieve or create nodes
        if len(expression) == 1:
            result = self.flatten(expression)
            if len(result) == 1:
                return result[0]
            else:
                concatNode = ConcatNode(",".join(expression))
                concatNode.listOfNodes += result
                return concatNode
            # mayExistNode = self.lookupTable.getKey(expression[0]) or self.findNode(expression[0])
            # if mayExistNode:
            #     return mayExistNode
            # return LiteralNode(expression[0], expression[0])

        # If we already created a Concat Node of the same arguments, then we can return that
        # mayExistNode = self.findNode(",".join(expression))
        # if mayExistNode:
        #     return mayExistNode

        concatNode = ConcatNode(",".join(expression))
        for expr in expression:
            concatNode.addNode(self.expand([expr]))
        return concatNode

    @staticmethod
    def convertOrGetConcatNode(node: Node):
        if isinstance(node, ConcatNode):
            return node
        newConcatNode = ConcatNode("CONCATED_" + node.getName())
        newConcatNode.addNode(node)
        return newConcatNode

    def export(self, writeToNeo=False):
        dot = Digraph(comment='SDG')
        clusterId = 0
        for cluster in self.getNodesCluster():
            newGraph = Digraph(name="cluster_" + str(clusterId))
            [newGraph.node(node.getName(), node.getNodeName(), shape=getNodeShape(node)) for node in cluster]
            visitedNodes = list()
            for node in cluster:
                if node in visitedNodes:
                    continue
                visitedNodes.append(node)
                if node.getChildren() is not None:
                    for child in node.getChildren():
                        newGraph.edge(node.getName(), child.getName(), label=getEdgeLabel(node, child))
            clusterId += 1
            dot.subgraph(newGraph)
        # Add all the nodes to the dot graph
        # nodes = self.getNodeSet()
        # [dot.node(node.getName(), node.getNodeName(), shape=getNodeShape(node)) for node in nodes]

        # Add edges
        # visitedNodes = list()
        # for node in nodes:
        #     if node in visitedNodes:
        #         continue
        #     visitedNodes.append(node)
        #     if node.getChildren() is not None:
        #         for child in node.getChildren():
        #             dot.edge(node.getName(), child.getName(), label=getEdgeLabel(node, child))

        dot.render('graph.gv', view=True)
        # Doing DFS to create nodes in NEO4j
        if writeToNeo:
            for node in self.getNodeSet():
                if node.dbNode:
                    continue
                self.exportToNeo(node)

    def exportToNeo(self, node: Node):
        if node.dbNode:
            return node.dbNode

        if isinstance(node, LiteralNode):
            dbNode = Literal(name=node.getName(), value=node.getValue()).save()
            node.dbNode = dbNode
            return dbNode

        if isinstance(node, RefNode):
            dbNode = Reference(name=node.getName()).save()
            refNode = self.exportToNeo(node.pointTo)
            dbNode.pointTo.connect(refNode)
            node.dbNode = dbNode
            return dbNode

        if isinstance(node, TargetNode):
            dbNode = Target(name=node.getName(), scope=node.scope).save()
            pointToDBNode = None
            definitionDBNode = None
            librariesDBNode = None
            if node.pointTo:
                pointToDBNode = self.exportToNeo(node.pointTo)
                dbNode.pointTo.connect(pointToDBNode)
            if node.definitions:
                definitionDBNode = self.exportToNeo(node.definitions)
                dbNode.definitions.connect(definitionDBNode)
            if node.linkLibraries:
                librariesDBNode = self.exportToNeo(node.linkLibraries)
                dbNode.linkLibraries.connect(librariesDBNode)

            node.dbNode = dbNode
            return dbNode

        if isinstance(node, ConcatNode):
            dbNode = Concat(name=node.getName()).save()
            for localNode in node.getNodes():
                dbNode.contains.connect(self.exportToNeo(localNode))
            node.dbNode = dbNode
            return dbNode

        if isinstance(node, SelectNode):
            dbNode = Select(name=node.getName(), condition=node.condition).save()
            if node.trueNode:
                dbNode.trueNode.connect(self.exportToNeo(node.trueNode))
            if node.falseNode:
                dbNode.falseNode.connect(self.exportToNeo(node.falseNode))
            node.dbNode = dbNode
            return dbNode

    def checkIntegrity(self):
        nodeNames = []
        for node in self.getNodeSet():
            if node.getName() in nodeNames:
                raise Exception("INTEGRITY CHECK FAILED!")
            nodeNames.append(node.getName())

    def findAndSetTargets(self):
        for node in self.getNodeSet():
            if isinstance(node, TargetNode):
                self.targets.add(node)
            if isinstance(node, TestNode):
                self.testTargets.add(node)

    def pathWithCondition(self, startNode, endNode, **kwargs):
        nodeToVisit = [startNode]
        visitedNode = []
        while nodeToVisit:
            node = nodeToVisit.pop()
            if node == endNode:
                return True
            if node in visitedNode:
                continue
            visitedNode.append(node)
            if node.getChildren() is not None:
                if isinstance(node, SelectNode):
                    conditions = {}
                    for expression in node.conditionList:
                        if expression in kwargs:
                            conditions[expression] = kwargs[expression]
                        else:
                            conditions[expression] = "UNDEFINED"
                    if False in conditions.values():
                        if node.falseNode:
                            nodeToVisit.append(node.falseNode)
                    elif "UNDEFINED" in conditions.values():
                        if node.falseNode:
                            nodeToVisit.append(node.falseNode)
                        if node.trueNode:
                            nodeToVisit.append(node.trueNode)
                    else:
                        nodeToVisit.append(node.trueNode)
                else:
                    nodeToVisit += node.getChildren()
        return False

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = VModel()

        return cls._instance

    @classmethod
    def clearInstance(cls):
        cls._instance = None


def getNodeShape(node: Node):
    if isinstance(node, SelectNode):
        return 'diamond'
    if isinstance(node, TargetNode):
        return 'box'
    if isinstance(node, ConcatNode):
        return 'doubleoctagon'
    if isinstance(node, CustomCommandNode):
        return 'parallelogram'
    if isinstance(node, TestNode):
        return 'component'
    if isinstance(node, RefNode):
        return 'cds'
    return 'ellipse'


def getEdgeLabel(firstNode: Node, secondNode: Node):
    if isinstance(firstNode, TargetNode):
        if firstNode.definitions == secondNode:
            return "Definitions"
        if firstNode.linkLibraries == secondNode:
            return "Libraries"
        if firstNode.pointTo == secondNode:
            return "Files"
    if isinstance(firstNode, SelectNode):
        if firstNode.trueNode == secondNode:
            return "TRUE"
        else:
            return "FALSE"

    return None
