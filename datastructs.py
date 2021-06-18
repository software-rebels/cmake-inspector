from operator import is_
from typing import Optional, List
import copy

from condition_data_structure import Rule

created_commands = dict()


class Node:

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        global created_commands
        if name in created_commands:
            created_commands[name] += 1
            self.name = "{}_{}".format(name, created_commands[name])
        else:
            created_commands[name] = 1
            self.name = name
        self.rawName = name
        self.parent: List[Optional[Node]] = []
        self.isVisited = False
        self.dbNode = None

    def getName(self):
        return self.name.replace('::', '->')

    def getNodeName(self):
        return self.getName()

    def getChildren(self) -> Optional[List]:
        return []

    def getNeighbours(self):
        if self.getChildren():
            return self.getChildren() + self.parent
        return self.parent

    # Useful for some graph algorithms
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
    
    # def __repr__(self):
    #     return str(self.__dict__)


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

    def addLinkLibrary(self, node: Node):
        if self.linkLibraries and isinstance(self.linkLibraries, ConcatNode):
            self.linkLibraries.addToBeginning(node)
        else:
            concatNode = ConcatNode("{}_libraries".format(self.getName()))
            concatNode.addNode(node)
            if self.linkLibraries:
                concatNode.addNode(self.linkLibraries)
            self.linkLibraries = concatNode

    def setDefinition(self, node: Node):
        self.definitions = node

    def getDefinition(self):
        return self.definitions

    def getValue(self):
        return self.name


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


# TODO: Use polymorphism here to implement CMake commands instead of handling all of them in evaluate function
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

    def getValue(self):
        commandsValue = [item.getValue() for item in self.commands]
        return f'{self.rawName}({" ".join(commandsValue)})'

    def evaluate(self, conditions, recStack, lookup=None):
        raise Exception('Deprecated')


class WhileCommandNode(CustomCommandNode):
    rule: Rule

    def __init__(self, rule: Rule):
        super(WhileCommandNode, self).__init__(rule.getCondition().getText(True))
        self.rule = rule


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
    rule: Rule = None

    def __init__(self, name, condition):
        super().__init__(name)
        self.trueNode: Optional[Node] = None
        self.falseNode: Optional[Node] = None
        self.conditionList = copy.deepcopy(condition)
        self.condition = " ".join(condition)
        self.args = None

    def getNodeName(self):
        return "SELECT\n" + self.rule.getCondition().getText(pretty=True)

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

    def getCondition(self):
        return self.rule.getCondition()

    def getValue(self):
        return f'if({self.rule.getCondition().getText(pretty=True)})'


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
            if key in self.items[-1]:  #
                del (self.items[-1][key])
            else:
                print(f"[WARNING] Called deleteKey without finding the key in lookup table for {key}")

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


class DirectoryNode(LiteralNode):
    def __init__(self, name):
        super().__init__(name)
        self._post_num = 0 # for linearization
        self.depends_on = [] # child
        self.depended_by = [] # parent
        self.targets = []


class DefinitionPair:
    def __init__(self, head, tail=None):
        self.head = head
        self.tail = tail


# Not much for now, but might have more in the future
# Technically not really a custom command, but the depends attribute is useful
class DefinitionNode(CustomCommandNode):
    def __init__(self, is_option=False, from_dir=True):
        super().__init__('local_definitions')
        # For now, is_option is useless
        self.is_option = is_option
        self.from_dir = from_dir


# Repeated flags need to be taken care of
# Might have unsatisfiable path in the graph for definitions.
class CommandDefinitionNode(CustomCommandNode):
    def __init__(self, command, is_option):
        if not command in ['add', 'remove']:
            raise ValueError(f'CommandDefinitionNode given wrong initialization input: {command}')
        name = ''
        if is_option is None:
            name = f'{command}_definitions'
        elif is_option:
            name = f'{command}_compile_options'
        else:
            name = f'{command}_compile_definitions'
        super().__init__(name)


class Directory:
    _instance = None

    def __init__(self):
        self.root = None
        self.map = {}
        self.topologicalOrder = None

    def setRoot(self, root_dir):
        self.root = DirectoryNode(root_dir)
        self.map[root_dir] = self.root

    def find(self, name):
        return self.map.get(name, None) 

    # Should also check for circular dependency when adding new child
    def addChild(self, node, child):
        node.depended_by.append(child)
        child.depends_on.append(node)
        self.map[child.name] = child

    def getTopologicalOrder(self, force=False):
        if self.topologicalOrder is not None and not force:
            return self.topologicalOrder
        self._dfs(self.root)
        sorted_nodes = sorted([(node, node._post_num) for _, node in self.map.items()], 
                                key=lambda x: x[1], reverse=True)
        result = [node for node, _ in sorted_nodes]
        return result

    def _dfs(self, node):
        def _visit(node):
            node.isVisited = True 
            for child in node.depends_on:
                if not child.isVisited:
                    _visit(child)
            _post(node)
        
        def _post(node):
            nonlocal post_num
            post_num += 1
            node._post_num = post_num
        
        post_num = 1
        _visit(node)

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = Directory()

        return cls._instance

    @classmethod
    def clearInstance(cls):
        cls._instance = None
