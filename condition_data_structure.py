import operator
from typing import Dict, List
from z3 import *


class LogicalExpression:
    logicType = None

    def __init__(self, logicType: str):
        self.logicType = logicType

    def getType(self):
        return self.logicType

    def getText(self, pretty=False) -> str:
        pass

    def evaluate(self):
        pass

    def satisfiable(self, condition: Dict) -> List:
        pass

    def getAssertions(self):
        pass

    def satModel(self, s: Solver):
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

    def getText(self, pretty=False):
        result = '{} OR {}'.format(self.getLeft().getText(pretty),
                                   self.getRight().getText(pretty))
        return result if pretty is False else "({})".format(result)

    def evaluate(self):
        return self.leftExpression.evaluate() or self.rightExpression.evaluate()

    def satisfiable(self, condition: Dict) -> List:
        # We convert OR to AND and use the same function we have for AND to avoid duplicates
        andEquivalent = NotExpression(AndExpression(NotExpression(self.getLeft()), NotExpression(self.getRight())))
        return andEquivalent.satisfiable(condition)

    def getAssertions(self):
        return simplify(Or(self.leftExpression.getAssertions(),
                           self.rightExpression.getAssertions()))


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

    def getText(self, pretty=False):
        result = '{} AND {}'.format(self.getLeft().getText(pretty),
                                    self.getRight().getText(pretty))
        return result if pretty is False else "({})".format(result)

    def evaluate(self):
        return self.leftExpression.evaluate() and self.rightExpression.evaluate()

    def satisfiable(self, condition: Dict) -> List:
        left_satisfiable = self.getLeft().satisfiable(condition)
        right_satisfiable = self.getRight().satisfiable(condition)
        result = []
        for l_sat in left_satisfiable:
            for r_sat in right_satisfiable:
                # We cannot merge two list of conditions with different values, like foo:True and foo:False
                contradiction = False
                for common_key in set(l_sat[1]).intersection(set(r_sat[1])):
                    if l_sat[1].get(common_key) != r_sat[1].get(common_key):
                        contradiction = True
                if contradiction:
                    continue

                # If left and right evaluated to True
                if l_sat[0] and r_sat[0]:
                    if (True, {**l_sat[1], **r_sat[1]}) not in result:
                        result.append((True, {**l_sat[1], **r_sat[1]}))
                    continue
                # If left and right evaluated to False, we only add one which is a subset of another
                if l_sat[0] is False and r_sat[0] is False:
                    if set(l_sat[1]).issubset(set(r_sat[1])):
                        if (False, l_sat[1]) not in result:
                            result.append((False, l_sat[1]))
                        continue
                    elif set(r_sat[1]).issubset(set(l_sat[1])):
                        if (False, r_sat[1]) not in result:
                            result.append((False, r_sat[1]))
                        continue
                if l_sat[0] is False and (False, l_sat[1]) not in result:
                    result.append((False, l_sat[1]))
                if r_sat[0] is False and (False, r_sat[1]) not in result:
                    result.append((False, r_sat[1]))

        return result

    def getAssertions(self):
        return simplify(And(self.leftExpression.getAssertions(),
                            self.rightExpression.getAssertions()))


class NotExpression(LogicalExpression):
    rightExpression: LogicalExpression = None

    def __init__(self, right: LogicalExpression):
        super(NotExpression, self).__init__('not')
        self.rightExpression = right

    def getRight(self):
        return self.rightExpression

    def getText(self, pretty=False):
        result = 'NOT {}'.format(self.getRight().getText(pretty))
        return result if pretty is False else "({})".format(result)

    def evaluate(self):
        return not self.rightExpression.evaluate()

    def satisfiable(self, condition: Dict) -> List:
        child_satisfiable = self.rightExpression.satisfiable(condition)
        result = []
        for item in child_satisfiable:
            result.append((not item[0], item[1]))
        return result

    def getAssertions(self):
        return simplify(Not(self.rightExpression.getAssertions()))


class LocalVariable(LogicalExpression):
    variableName: str = None
    variable: [Bool, Int, String] = None

    def __init__(self, variableName, varType='bool'):
        super(LocalVariable, self).__init__('var')
        self.variableName = variableName
        if varType == 'bool':
            self.variable = Bool(variableName)
        elif varType == 'int':
            self.variable = Int(variableName)
        elif varType == 'string':
            self.variable = String(variableName)

    def getText(self, pretty=False):
        return "${{{}}}".format(self.variableName)

    def toInt(self):
        self.variable = Int(self.variableName)

    def toString(self):
        self.variable = String(self.variableName)

    def evaluate(self):
        # TODO: Given the fact, we should evaluate this last piece in the evaluate tree
        pass

    def satisfiable(self, condition: Dict) -> List:
        # First check if we have a fact about the variable
        if self.variableName in condition:
            return [(condition[self.variableName], {})]
        return [
            (True, {self.variableName: True}),
            (False, {self.variableName: False})
        ]

    def getAssertions(self):
        return self.variable


class ConstantExpression(LogicalExpression):
    value: str = None

    def __init__(self, value):
        super(ConstantExpression, self).__init__('constant')
        self.value = value

    def getText(self, pretty=False):
        return self.value

    def evaluate(self):
        if self.value.lower() in ('false', 'no'):
            return False
        return True

    def satisfiable(self, condition: Dict) -> List:
        return [(self.evaluate(), {})]

    def getAssertions(self):
        return self.value


class ComparisonExpression(LogicalExpression):
    leftExpression: LogicalExpression = None
    rightExpression: LogicalExpression = None

    def __init__(self, left: LogicalExpression, right: LogicalExpression, operator):
        super(ComparisonExpression, self).__init__(operator)
        self.leftExpression = left
        self.rightExpression = right

    def getLeft(self):
        return self.leftExpression

    def getRight(self):
        return self.rightExpression

    def getText(self, pretty=False):
        result = '{} {} {}'.format(self.getLeft().getText(pretty),
                                   self.logicType,
                                   self.getRight().getText(pretty))
        return result if pretty is False else "({})".format(result)

    def satisfiable(self, condition: Dict) -> List:
        return [(False, {})]

    def returnOperator(self):
        if self.logicType == 'GREATER':
            return operator.gt

    def getAssertions(self):
        return simplify(self.returnOperator()(self.leftExpression.getAssertions(),
                                              self.rightExpression.getAssertions()))


class Rule:
    type: str = None
    level: int = None
    args: list = None
    condition: LogicalExpression = None
    flattenedResult: list = [set()]

    def setCondition(self, condition: LogicalExpression):
        self.condition = condition
        self.args = self.getText().split()

    def getCondition(self) -> LogicalExpression:
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
