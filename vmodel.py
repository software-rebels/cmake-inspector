import copy
import re
from typing import Optional, List, Set

from graphviz import Digraph

import datastructs
from condition_data_structure import Rule
from datalayer import Definition, Literal, Reference, Target, Concat, Select, CustomCommand, Option
from datastructs import DefinitionNode, LiteralNode, Node, Lookup, RefNode, SelectNode, TargetNode, TestNode, ConcatNode, \
    CustomCommandNode, OptionNode
from graph_illustration import getNodeShape, getEdgeLabel

VARIABLE_REGEX = r"\${(\S*)}"

def infinite_sequence():
    num = 0
    while True:
        yield num
        num += 1

class VModel:
    _instance = None
    RESERVED_NODES = {
        'NOT': LiteralNode('NOT'),
        'OR': LiteralNode('OR')
    }

    def __init__(self):
        Node.created_commands = dict()
        self.flattenMemoize = {}
        self.nodes: Optional[List[Node]] = []
        self.cmakeVersion = None
        self.ifLevel = 0
        self.ifConditions = []
        self.targets = set()
        self.testTargets = set()
        self.options = dict()
        self.lookupTable = Lookup.getInstance()
        self.recordCommands = False
        self.COUNTER = infinite_sequence()
        self.tmpLookupTableStack = []
        self.systemState: List[Rule] = []
        self.functions = {}
        self.currentFunctionCommand = None
        # Defined properties
        self.definedProperties = {
            'GLOBAL': {},
            'DIRECTORY': {},
            'TARGET': {},
            'SOURCE': {},
            'TEST': {},
            'VARIABLE': {},
            'CACHED_VARIABLE': {}
        }
        # These data structures are for properties related to a directory
        self.directory_to_properties = {'.': Lookup()}
        self.DIRECTORY_PROPERTIES = self.directory_to_properties.get('.')
        self.DIRECTORY_PROPERTIES.setKey('VARIABLES', self.lookupTable.items[-1])
        # A temp variable to keep changes between nodes
        self.nodeStack = []
        # A new property to support nested if statements
        self.ifLevel = 0
        self.definitionOrder = 0

    def pushSystemState(self, rule: Rule):
        self.systemState.append(rule)

    def getCurrentSystemState(self) -> Optional[Rule]:

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

    def getDefinitionOrder(self):
        self.definitionOrder += 1
        return self.definitionOrder

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
        # Some reserved keywords like NOT AND OR etc use too many times. We don't want to search for them nor
        # Create a new node. Also, if a keyword used more than one for the first time in a string, like
        # A AND B AND C, previously this function created two AND because cannot find the first one.
        if name in self.RESERVED_NODES:
            return self.RESERVED_NODES.get(name)
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
                # Create an empty RefNode for variables which are not defined like ${CMAKE_CURRENT_BINARY_DIR}
                if not node:
                    node = RefNode("{}".format(variableName[0]), None)
                    self.lookupTable.setKey("${{{}}}".format(variableName[0]), node)
                # if not isinstance(node, RefNode):
                    # raise Exception("NOT_IMPLEMENTED")
                result.append(node)
            else:
                # We might have a target with the same name
                node = self.lookupTable.getKey(f't:{item}')
                if not node:
                    node = self.findNode(item)
                if not node:
                    node = LiteralNode(item, item)
                result.append(node)
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

    def expand(self, expression: List[str], forceConcatNode=False) -> Node:
        # A recursive function which retrieve or create nodes
        if len(expression) == 1:
            result = self.flatten(expression)
            if len(result) == 1 and not forceConcatNode:
                return result[0]
            else:
                concatNode = ConcatNode("{}".format(",".join(expression)))
                concatNode.listOfNodes += result
                concatNode.concatString = True
                return concatNode

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

    def export(self, writeToNeo=False, writeDotFile=True):
        if writeDotFile:
            dot = Digraph(comment='SDG')
            dot.graph_attr['ordering'] = 'out'
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
            dot.render('graph.gv', view=True)
        
        # Doing DFS to create nodes in NEO4j
        if writeToNeo:
            for node in self.getNodeSet():
                if node.dbNode:
                    continue
                self.exportToNeo(node)

    def exportToNeo(self, node: Node):
        dbNode = node.dbNode
        if dbNode:
            return dbNode

        if isinstance(node, LiteralNode):
            dbNode = Literal(name=node.getName(), value=node.getValue()).save()
            node.dbNode = dbNode
        
        if isinstance(node, OptionNode):
            dbNode = Option(name=node.getName()).save()
            node.dbNode = dbNode
        
        if isinstance(node, RefNode):
            dbNode = Reference(name=node.getName()).save()
            if node.getPointTo():
                refNode = self.exportToNeo(node.getPointTo())
                dbNode.pointTo.connect(refNode)
            node.dbNode = dbNode
        
        if isinstance(node, TargetNode):
            dbNode = Target(name=node.rawName, scope=node.scope).save()
            pointToDBNode = None
            definitionDBNode = None
            librariesDBNode = None
            if node.sources:
                pointToDBNode = self.exportToNeo(node.sources)
                dbNode.pointTo.connect(pointToDBNode)
            if node.definitions:
                definitionDBNode = self.exportToNeo(node.definitions)
                dbNode.definitions.connect(definitionDBNode)
            if node.linkLibraries:
                librariesDBNode = self.exportToNeo(node.linkLibraries)
                dbNode.linkLibraries.connect(librariesDBNode)

            properties = {
                'isExecutable': node.isExecutable,
                'isAlias': node.isAlias,
                'imported': node.imported,
                'isObjectLibrary': node.isObjectLibrary,
                'interfaceLibrary': node.interfaceLibrary,
                'isCustomTarget': node.isCustomTarget,
                'defaultBuildTarget': node.defaultBuildTarget,
                'libraryType': node.libraryType,
            }

            dbNode.properties = properties
            node.dbNode = dbNode
        
        if isinstance(node, ConcatNode):
            dbNode = Concat(name=node.getName()).save()
            for localNode in node.getNodes():
                dbNode.contains.connect(self.exportToNeo(localNode))
            node.dbNode = dbNode
        
        if isinstance(node, SelectNode):
            dbNode = Select(name=node.getName()).save()
            if node.trueNode:
                dbNode.trueNode.connect(self.exportToNeo(node.trueNode))
            if node.falseNode:
                dbNode.falseNode.connect(self.exportToNeo(node.falseNode))
            dbNode.condition.connect(self.exportToNeo(node.args))
            node.dbNode = dbNode
        
        if isinstance(node, CustomCommandNode):
            dbNode = CustomCommand(name=node.getName()).save()
            for localNode in node.commands:
                if localNode is None:
                    continue
                dbNode.commands.connect(self.exportToNeo(localNode))
            for localNode in node.depends:
                if localNode is None:
                    continue
                dbNode.depends.connect(self.exportToNeo(localNode))
            dbNode.extraInfo = node.extraInfo
        
        if isinstance(node, DefinitionNode):
            dbNode = Definition(name=node.getName()).save()
            for localNode in node.commands:
                if localNode is None:
                    continue
                dbNode.commands.connect(self.exportToNeo(localNode))
            for localNode in node.depends:
                if localNode is None:
                    continue
                dbNode.depends.connect(self.exportToNeo(localNode))
            dbNode.from_dir = node.from_dir
            dbNode.ordering = node.ordering
            for localNode in node.inherits:
                if localNode is None:
                    continue
                dbNode.inherits.connect(self.exportToNeo(localNode))
                
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

    def getLibrariesForTarget(self):
        pass


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
        datastructs.created_commands = dict()
        cls._instance = None
