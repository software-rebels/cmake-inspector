from enum import Enum, auto
from typing import Optional, List, Set, Dict
from graphviz import Digraph
import copy
from datalayer import Target, Reference, Concat, Literal, Select, CustomCommand
import re
import glob
import os
import logging

logging.basicConfig(filename='cmakeInspector.log', level=logging.DEBUG)

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
    created_commands = dict()

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if name in self.created_commands:
            self.created_commands[name] += 1
            self.name = "{}_{}".format(name, self.created_commands[name])
        else:
            self.created_commands[name] = 1
            self.name = name
        self.rawName = name
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

    def __eq__(self, other):
        if other is None:
            return False
        return self.name == other.name


class FinalTarget(Node):

    def __init__(self, name):
        super().__init__(name)
        self.files: Optional[Node] = None

    def getChildren(self) -> Optional[List]:
        return [self.files]


class FinalConcatNode(Node):

    def __init__(self, name):
        super().__init__(name)
        self.children = []

    def getChildren(self) -> Optional[List]:
        return self.children


class FinalSelectNode(Node):

    def __init__(self, name):
        super().__init__(name)
        self.children = []

    def getNodeName(self):
        return "SELECT"

    def addChild(self, item):
        self.children.append(item)

    def getLabel(self, item):
        for child in self.children:
            if child[0] == item:
                return child[1]

    def getChildren(self) -> Optional[List]:
        result = []
        for item in self.children:
            result.append(item[0])
        return result


class TargetNode(Node):
    STATIC_LIBRARY = 'STATIC'
    SHARED_LIBRARY = 'SHARED'
    MODULE_LIBRARY = 'MODULE'

    def __init__(self, name: str, sources: Node):
        super().__init__(name)
        self.sources = sources  # Property of Target
        self.interfaceSources = None  # Property of Target
        self.compileFeatures = None  # Property of Target
        self.interfaceCompileFeatures = None  # Property of Target
        self.compileOptions = None  # Property of Target
        self.interfaceCompileOptions = None  # Property of Target
        self.includeDirectories = None  # Property of Target
        self.interfaceIncludeDirectories = None  # Property of Target
        self.interfaceSystemIncludeDirectories = None  # Property of Target
        self.definitions = None
        self.linkLibraries = None

        self.scope = None
        self.imported = False
        self.isAlias = False
        # This property indicates whether this is an executable or a library
        self.isExecutable = True
        # These properties are for libraries only
        self.libraryType = self.STATIC_LIBRARY
        self.isObjectLibrary = False
        self.interfaceLibrary = False
        # This property set for custom target only
        self.isCustomTarget = False
        # This property is for custom target indicating whether this target should compiled by
        # default or not
        self.defaultBuildTarget = False

        # This dictionary will keep track of the libraries that this target may depend on under different conditions
        # <CustomCommand (target_link_libraries command), condition: Set>
        self.linkLibrariesConditions = dict()

    def getPointTo(self) -> Node:
        return self.sources

    def getChildren(self):
        result = []
        if self.sources:
            result.append(self.sources)
        if self.definitions:
            result.append(self.definitions)
        if self.linkLibraries:
            result.append(self.linkLibraries)
        if self.interfaceSources:
            result.append(self.interfaceSources)
        if self.compileFeatures:
            result.append(self.compileFeatures)
        if self.interfaceCompileFeatures:
            result.append(self.interfaceCompileFeatures)
        if self.compileOptions:
            result.append(self.compileOptions)
        if self.interfaceCompileOptions:
            result.append(self.interfaceCompileOptions)
        if self.includeDirectories:
            result.append(self.includeDirectories)
        if self.interfaceIncludeDirectories:
            result.append(self.interfaceIncludeDirectories)
        if self.interfaceSystemIncludeDirectories:
            result.append(self.interfaceSystemIncludeDirectories)
        return result

    def addLinkLibrary(self, node: Node, autoGeneratedNumber):
        if self.linkLibraries and isinstance(self.linkLibraries, ConcatNode):
            self.linkLibraries.addToBeginning(node)
        else:
            concatNode = ConcatNode("{}_{}".format(self.getName(), autoGeneratedNumber))
            concatNode.addNode(node)
            if self.linkLibraries:
                concatNode.addNode(self.linkLibraries)
            self.linkLibraries = concatNode

    def setDefinition(self, node: Node):
        self.definitions = node

    def getDefinition(self):
        return self.definitions


class TestNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.command = None
        self.configurations = None
        self.working_directory = None

    def getChildren(self):
        result = [self.command]
        if self.configurations:
            result.append(self.configurations)
        if self.working_directory:
            result.append(self.working_directory)
        return result


class RefNode(Node):
    def __init__(self, name: str, pointTo: Optional[Node]):
        super().__init__(name)
        self.pointTo = pointTo
        self.relatedProperty = None

    def getPointTo(self) -> Node:
        return self.pointTo

    def getChildren(self):
        if self.pointTo:
            return [self.pointTo]
        return []

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
        if self.getPointTo():
            return self.pointTo.getName()
        return self.getName()[:self.getName().rindex('_')]


class OptionNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.depends: Optional[Node] = None
        self.description: Optional[str] = None
        self.default: bool = False
        self.dependentOption: Optional[bool] = False

    def getPointTo(self) -> Node:
        return self.depends

    def getChildren(self):
        if self.depends:
            return [self.depends]
        return []

    def getValue(self):
        return self.getName()


class CustomCommandNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.commands: List[Node] = []
        self.depends: List[Node] = []
        # For backward compatibility
        self.pointTo = self.commands
        self.extraInfo = {}

    def getChildren(self) -> Optional[List]:
        result = []
        if self.commands:
            result += self.commands
        if self.depends:
            result += self.depends
        if result:
            return result
        return None

    def evaluate(self, conditions, recStack, lookup = None):
        print("##### Start evaluating custom command " + self.rawName)
        if conditions is None:
            conditions = set()

        if 'file' in self.getName().lower():
            arguments = self.commands[0].getChildren()
            fileCommandType = arguments[0].getValue()
            if fileCommandType.upper() == 'GLOB':
                arguments = flattenAlgorithmWithConditions(self.commands[0].getChildren()[1],
                                                           conditions, recStack=recStack)
                result = []
                for arg in arguments:
                    wildcardPath = re.findall('"(.*)"', arg[0])
                    if wildcardPath:
                        wildcardPath = wildcardPath[0]
                    else:
                        wildcardPath = arg[0]
                    for item in glob.glob(os.path.join(self.extraInfo.get('pwd'), wildcardPath)):
                        result.append([item, arg[1]])
                return result
        elif 'target_link_libraries' in self.rawName.lower():
            result = []
            arguments = self.commands[0].getChildren()[1:]
            for argument in arguments:
                for item in flattenAlgorithmWithConditions(argument, conditions, recStack=recStack):
                    node = VModel.getInstance().lookupTable.getKey("t:{}".format(item[0]))
                    if isinstance(node, TargetNode):
                        result += flattenAlgorithmWithConditions(node.sources, item[1], recStack=recStack)
                        for library, conditions in node.linkLibrariesConditions.items():
                            result += flattenAlgorithmWithConditions(library, conditions.union(item[1]),
                                                                     recStack=recStack)
            return result


class ConcatNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.listOfNodes = list()
        self.concatString = False

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

    def getValue(self):
        result = []
        for child in self.getChildren():
            result.append(str(child.getValue()))
        if self.concatString:
            return "".join(result)
        else:
            return " ".join(result)


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
        self.args = None

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
        if self.args:
            result.append(self.args)
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

    def getOwnKey(self, key) -> Optional[Node]:
        lastTable = self.items[-1]
        return lastTable.get(key, None)

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


def flattenAlgorithmWithConditions(node: Node, conditions: Set = None, debug=True, recStack=None, useCache=False):
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
    if node in VModel.getInstance().flattenMemoize and useCache:
        flattedResult = copy.copy(VModel.getInstance().flattenMemoize[node])
    elif isinstance(node, LiteralNode):
        flattedResult = [(node.getValue(), conditions)]
    elif isinstance(node, TargetNode):
        flattedResult = [(node.rawName, conditions)]
    elif isinstance(node, RefNode):
        # If RefNode is a symbolic node, it may not have point to attribute
        if node.getPointTo() is None:
            flattedResult = [(node.rawName, conditions)]
        else:
            flattedResult = flattenAlgorithmWithConditions(node.getPointTo(), None, debug, recStack)
    elif isinstance(node, CustomCommandNode):
        flattedResult = node.evaluate(None, recStack)
    elif isinstance(node, SelectNode):
        if node.falseNode and node.trueNode:
            flattedResult = flattenAlgorithmWithConditions(node.falseNode, {(node.args, False)}, debug, recStack) + \
                   flattenAlgorithmWithConditions(node.trueNode, {(node.args, True)}, debug, recStack)
        elif node.trueNode:
            flattedResult = flattenAlgorithmWithConditions(node.trueNode, {(node.args, True)}, debug, recStack)
        elif node.falseNode:
            flattedResult = flattenAlgorithmWithConditions(node.falseNode, {(node.args, False)}, debug, recStack)
    elif isinstance(node, ConcatNode):
        result = ['']
        for item in node.getChildren():
            childSet = flattenAlgorithmWithConditions(item, None, debug, recStack)
            tempSet = []
            if childSet is None:
                continue

            # There are two types of concat node. One which concat the literal string
            # and other one which make a list of values
            if node.concatString:
                for str1 in result:
                    for str2 in childSet:
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

    if node not in VModel.getInstance().flattenMemoize:
        VModel.getInstance().flattenMemoize[node] = copy.copy(flattedResult)

    recStack.remove(node)

    if flattedResult:
        for item in flattedResult:
            item[1].update(conditions)
    return flattedResult


# Given a Node (often a ConcatNode) this algorithm will return flatted arguments
def getFlattedArguments(argNode: Node):
    result = []
    if isinstance(argNode, LiteralNode):
        return [argNode.getValue()]
    for arg in argNode.getChildren():
        result.append("".join(flattenAlgorithm(arg)))
    return result


class VModel:
    _instance = None

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
        self.systemState = []
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

    def pushSystemState(self, state, properties):
        self.systemState.append((state, properties, self.ifLevel))

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
                # Create an empty RefNode for variables which are not defined like ${CMAKE_CURRENT_BINARY_DIR}
                if not node:
                    node = RefNode("{}_{}".format(variableName[0], self.getNextCounter()), None)
                    self.lookupTable.setKey("${{{}}}".format(variableName[0]), node)
                if not isinstance(node, RefNode):
                    raise Exception("NOT_IMPLEMENTED")
                result.append(node)
            else:
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
        if node.dbNode:
            return node.dbNode

        if isinstance(node, LiteralNode):
            dbNode = Literal(name=node.getName(), value=node.getValue()).save()
            node.dbNode = dbNode
            return dbNode

        if isinstance(node, RefNode):
            dbNode = Reference(name=node.getName()).save()
            if node.getPointTo():
                refNode = self.exportToNeo(node.getPointTo())
                dbNode.pointTo.connect(refNode)
            node.dbNode = dbNode
            return dbNode

        if isinstance(node, TargetNode):
            dbNode = Target(name=node.getName(), scope=node.scope).save()
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
    if isinstance(node, OptionNode):
        return 'larrow'
    return 'ellipse'


def getEdgeLabel(firstNode: Node, secondNode: Node):
    if isinstance(firstNode, TargetNode):
        if firstNode.definitions == secondNode:
            return "Definitions"
        if firstNode.linkLibraries == secondNode:
            return "Libraries"
        if firstNode.sources == secondNode:
            return "Sources"
        if firstNode.interfaceSources == secondNode:
            return "Interface_sources"
        if firstNode.compileFeatures == secondNode:
            return "Compile_features"
        if firstNode.interfaceCompileFeatures == secondNode:
            return "Interface_compile_features"
        if firstNode.compileOptions == secondNode:
            return "Compile_options"
        if firstNode.interfaceCompileFeatures == secondNode:
            return "Interface_compile_options"
        if firstNode.includeDirectories == secondNode:
            return "INCLUDE_DIRECTORIES"
        if firstNode.interfaceIncludeDirectories == secondNode:
            return "INTERFACE_INCLUDE_DIRECTORIES"
        if firstNode.interfaceSystemIncludeDirectories == secondNode:
            return "INTERFACE_SYSTEM_INCLUDE_DIRECTORIES"
    if isinstance(firstNode, SelectNode):
        if firstNode.trueNode == secondNode:
            return "TRUE"
        elif firstNode.falseNode == secondNode:
            return "FALSE"
        elif firstNode.args == secondNode:
            return "CONDITION"
    if isinstance(firstNode, OptionNode):
        if firstNode.depends == secondNode:
            return 'DEPENDS'
    if isinstance(firstNode, FinalSelectNode):
        return firstNode.getLabel(secondNode)
    if isinstance(firstNode, FinalTarget):
        if firstNode.files == secondNode:
            return "FILES"
    if isinstance(firstNode, RefNode):
        return firstNode.relatedProperty

    return None
