class LogicalExpression:
    logicType = None

    def __init__(self, logicType: str):
        self.logicType = logicType

    def getType(self):
        return self.logicType

    def getText(self) -> str:
        pass

    def evaluate(self):
        pass


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

    def getText(self):
        return '{} OR {}'.format(self.getLeft().getText(),
                                 self.getRight().getText())

    def evaluate(self):
        return self.leftExpression.evaluate() or self.rightExpression.evaluate()


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

    def getText(self):
        return '{} AND {}'.format(self.getLeft().getText(),
                                  self.getRight().getText())

    def evaluate(self):
        return self.leftExpression.evaluate() and self.rightExpression.evaluate()


class NotExpression(LogicalExpression):
    rightExpression: LogicalExpression = None

    def __init__(self, right: LogicalExpression):
        super(NotExpression, self).__init__('not')
        self.rightExpression = right

    def getRight(self):
        return self.rightExpression

    def getText(self):
        return 'NOT {}'.format(self.getRight().getText())

    def evaluate(self):
        return not self.rightExpression.evaluate()


class LocalVariable(LogicalExpression):
    variableName: str = None

    def __init__(self, variableName):
        super(LocalVariable, self).__init__('var')
        self.variableName = variableName

    def getText(self):
        return self.variableName

    def evaluate(self):
        # TODO: Given the fact, we should evaluate this last piece in the evaluate tree
        pass


class ConstantExpression(LogicalExpression):
    value: str = None

    def __init__(self, value):
        super(ConstantExpression, self).__init__('constant')
        self.value = value

    def getText(self):
        return self.value

    def evaluate(self):
        if self.value.lower() in ('false', 'no'):
            return False
        return True


class Rule:
    type: str = None
    level: int = None
    args: list = None
    condition: LogicalExpression = None

    def setCondition(self, condition: LogicalExpression):
        self.condition = condition
        self.args = self.getText().split()

    def getCondition(self):
        return self.condition

    def setType(self, type: str):
        self.type = type

    def getType(self):
        return self.type

    def setLevel(self, level: int):
        self.level = level

    def setArgs(self, args: list):
        self.args = args

    def getArgs(self):
        return self.args

    def getText(self):
        return self.condition.getText()

