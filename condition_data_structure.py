class LogicalExpression:
    logicType = None

    def __init__(self, logicType: str):
        self.logicType = logicType

    def getType(self):
        return self.logicType


class OrExpression(LogicalExpression):
    leftExpression: LogicalExpression = None
    rightExpression: LogicalExpression = None

    def __init__(self, left: LogicalExpression, right: LogicalExpression):
        super(OrExpression, self).__init__('or')
        self.leftExpression = left
        self.rightExpression = right

    def getLeft(self):
        return self.leftExpression

    def getRight(self):
        return self.rightExpression


class AndExpression(LogicalExpression):
    leftExpression: LogicalExpression = None
    rightExpression: LogicalExpression = None

    def __init__(self, left: LogicalExpression, right: LogicalExpression):
        super(AndExpression, self).__init__('and')
        self.leftExpression = left
        self.rightExpression = right

    def getLeft(self):
        return self.leftExpression

    def getRight(self):
        return self.rightExpression


class NotExpression(LogicalExpression):
    rightExpression: LogicalExpression = None

    def __init__(self, right: LogicalExpression):
        super(NotExpression, self).__init__('not')
        self.rightExpression = right

    def getRight(self):
        return self.rightExpression


class LocalVariable(LogicalExpression):
    variableName: str = None

    def __init__(self, variableName):
        super(LocalVariable, self).__init__('var')
        self.variableName = variableName


class Rule:
    type: str = None
    level: int = None
    args: list = None
    condition: LogicalExpression = None

    def setCondition(self, condition: LogicalExpression):
        self.condition = condition

    def setType(self, type: str):
        self.type = type

    def setLevel(self, level: int):
        self.level = level

    def setArgs(self, args: list):
        self.args = args

