from datastructs import *


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
    if isinstance(firstNode, CustomCommandNode):
        if firstNode.commands and firstNode.commands[0] == secondNode:
            return "COMMANDS"
        elif firstNode.depends and firstNode.depends[0] == secondNode:
            return "DEPENDS"
    if isinstance(firstNode, OptionNode):
        if firstNode.depends == secondNode:
            return 'DEPENDS'
    if isinstance(firstNode, RefNode):
        return firstNode.relatedProperty

    return None
