from neomodel import StructuredNode, StringProperty, RelationshipTo, RelationshipFrom


class AbstractNode(StructuredNode):
    __abstract_node__ = True
    name = StringProperty(unique_index=True, required=True)


class Target(AbstractNode):
    pointTo = RelationshipTo(AbstractNode, "FILES")
    definitions = RelationshipTo(AbstractNode, "DEFINITIONS")
    linkLibraries = RelationshipTo(AbstractNode, "LIBRARIES")
    scope = StringProperty()


class Reference(AbstractNode):
    pointTo = RelationshipTo(AbstractNode, "DEPEND")


class Concat(AbstractNode):
    contains = RelationshipTo(AbstractNode, "DEPEND")


class Literal(AbstractNode):
    value = StringProperty()


class Select(AbstractNode):
    trueNode = RelationshipTo(AbstractNode, "TRUE")
    falseNode = RelationshipTo(AbstractNode, "FALSE")
    condition = StringProperty()
