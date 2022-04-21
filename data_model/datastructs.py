from operator import is_
from typing import Optional, List, Type
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
        self.interfaceDefinitions = None  # Not sure if we need this yet
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

        # This list will contain the other target nodes that this node depends on and they have to be compiled before this one
        self.depends = []; 
        
    def getPointTo(self) -> Node:
        return self.sources

    def getChildren(self):
        result = []
        if self.sources:
            result.append(self.sources)
        if self.definitions:
            result.append(self.definitions)
        if self.interfaceDefinitions:
            result.append(self.interfaceDefinitions)
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

    def setInterfaceDefinition(self, node: Node):
        self.interfaceDefinitions = node

    def getDefinition(self):
        return self.definitions

    def setCompileOptions(self, node: Node):
        self.compileOptions = node

    def setInterfaceCompileOptions(self, node: Node):
        self.interfaceCompileOptions = node

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

class ForeachCommandNode(CustomCommandNode):
    loopVariableName:str;
    iterationVariableName:Node;
    def __init__(self,loopVariableName:str,iterationVariableName:Node):
        super(ForeachCommandNode, self).__init__('foreach');
        self.loopVariableName = loopVariableName
        self.iterationVariableName= iterationVariableName

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
        if parentScope and len(self.items) > 1:
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
        return self.variableHistory.get(key)

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
        self.depends_on = [] # child depends on parent
        self.depended_by = [] # parent depended by child
        self.targets = []


class DefinitionPair:
    def __init__(self, head, tail=None):
        self.head = head
        self.tail = tail


# Technically not really a custom command, but node type integrates well
class DefinitionNode(CustomCommandNode):
    def __init__(self, from_dir=True, ordering=-1):
        super().__init__(f"{'directory' if from_dir else 'target'}_definitions")
        self.from_dir = from_dir
        self.ordering = ordering # For figuring out add/remove dependencies.
        self.inherits = []

    def addInheritance(self, node):
        if not isinstance(node, DefinitionNode):
            raise TypeError("Inherited node is not of type DefinitionNode.")
        self.inherits.append(node)
    
    def getChildren(self) -> Optional[List]:
        result = []
        result.extend(self.inherits)
        if r := super().getChildren():
            result.extend(r)
        return result if result else None


class CommandDefinitionNode(CustomCommandNode):
    def __init__(self, command, specific=False):
        self.command_type = command
        if not command in ['add', 'remove']:
            raise ValueError(f'CommandDefinitionNode given wrong initialization input: {command}')
        name = ''
        if specific:
            name = f'{command}_compile_definitions'
        else:
            name = f'{command}_definitions'
        super().__init__(name)


class TargetCompileDefinitionNode(CustomCommandNode):
    def __init__(self):
        super().__init__('target_compile_definitions')


class Directory:
    _instance = None

    def __init__(self):
        self.root = None
        self.map = {}
        # might want to test linearization later, but ignore for now.
        self.topologicalOrder = None 

    def setRoot(self, root_dir):
        if not self.root:
            self.root = DirectoryNode(root_dir)
            self.map[root_dir] = self.root

    def find(self, name):
        return self.map.get(name, None) 

    # TODO: Should also check for circular dependency when adding new child
    def addChild(self, node, child):
        node.depended_by.append(child)
        child.depends_on.append(node)
        self.map[child.rawName] = child

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
