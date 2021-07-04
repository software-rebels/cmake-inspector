from datastructs import CustomCommandNode
from neomodel import StructuredNode, StringProperty, IntegerProperty, RelationshipTo, RelationshipFrom, JSONProperty


class AbstractNode(StructuredNode):
    @classmethod
    def category(cls):
        pass

    __abstract_node__ = True
    name = StringProperty(unique_index=True, required=True)


class Target(AbstractNode):
    pointTo = RelationshipTo(AbstractNode, "FILES")
    definitions = RelationshipTo(AbstractNode, "DEFINITIONS")
    linkLibraries = RelationshipTo(AbstractNode, "LIBRARIES")
    scope = StringProperty()
    properties = JSONProperty()


class CustomCommand(AbstractNode):
    commands = RelationshipTo(AbstractNode, 'COMMANDS')
    depends = RelationshipTo(AbstractNode, 'DEPENDS')
    extraInfo = JSONProperty()


# Might have to add more specific CustomCommandNode when the polymorphism
# becomes more complicated
class Definition(CustomCommand):
    from_dir = StringProperty()
    ordering = IntegerProperty()
    inherits = RelationshipTo(AbstractNode, 'INHERITS')


class Reference(AbstractNode):
    pointTo = RelationshipTo(AbstractNode, "DEPEND")


class Concat(AbstractNode):
    contains = RelationshipTo(AbstractNode, "DEPEND")


class Literal(AbstractNode):
    value = StringProperty()


class Select(AbstractNode):
    trueNode = RelationshipTo(AbstractNode, "TRUE")
    falseNode = RelationshipTo(AbstractNode, "FALSE")
    condition = RelationshipTo(AbstractNode, 'CONDITION')


class Option(AbstractNode):
    value = StringProperty()
