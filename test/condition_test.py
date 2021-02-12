import unittest
from condition_data_structure import *


class TestConditions(unittest.TestCase):
    def setUp(self) -> None:
        self.fooVar = LocalVariable('foo')
        self.barVar = LocalVariable('bar')
        self.johnVar = LocalVariable('john')
        self.doeVar = LocalVariable('doe')

    def test_local_variable_satisfiable_true(self):
        conditions = {
            'foo': True
        }
        # foo
        self.assertCountEqual(
            [(True, {})], self.fooVar.satisfiable(conditions)
        )

    def test_local_variable_satisfiable_false(self):
        conditions = {
            'foo': False
        }
        # foo
        self.assertCountEqual(
            [(False, {})], self.fooVar.satisfiable(conditions)
        )

    def test_local_variable_satisfiable_unknown(self):
        conditions = {
            'bar': True
        }
        # foo
        self.assertCountEqual(
            [(True, {'foo': True}), (False, {'foo': False})], self.fooVar.satisfiable(conditions)
        )

    def test_not_satisfiable(self):
        conditions = {
            'bar': True
        }
        # NOT foo
        notExpression = NotExpression(self.fooVar)
        self.assertCountEqual(
            [(False, {'foo': True}), (True, {'foo': False})], notExpression.satisfiable(conditions)
        )

    def test_and_satisfiable_true(self):
        conditions = {
            'foo': True,
            'bar': True
        }
        # foo AND bar
        andExpression = AndExpression(self.fooVar, self.barVar)
        self.assertCountEqual(
            [(True, {})], andExpression.satisfiable(conditions)
        )

    def test_and_satisfiable_false(self):
        conditions = {
        }
        # foo AND bar
        andExpression = AndExpression(self.fooVar, self.barVar)
        self.assertCountEqual(
            [(False, {})], andExpression.satisfiable(conditions)
        )

    def test_and_satisfiable_false_triple_statement(self):
        conditions = {
            'foo': False
        }
        # (foo AND bar) AND john
        andEx1 = AndExpression(self.fooVar, self.barVar)
        andEx2 = AndExpression(andEx1, self.johnVar)
        self.assertCountEqual(
            [(False, {})], andEx2.satisfiable(conditions)
        )

    def test_and_satisfiable_without_condition(self):
        andEx1 = AndExpression(self.fooVar, self.barVar)
        # (foo AND bar) AND NOT(NOT foo AND NOT bar)
        expression = AndExpression(andEx1,
                                   NotExpression(AndExpression(NotExpression(self.fooVar),
                                                               NotExpression(self.barVar))))
        self.assertCountEqual(
            [
                (True, {'foo': True, 'bar': True}), (False, {'foo': False}), (False, {'bar': False})
            ], expression.satisfiable({})
        )

    def test_or_satisfiable_true(self):
        condition = {
            'foo': True
        }
        orExp = OrExpression(self.fooVar, self.barVar)
        # foo OR bar
        self.assertCountEqual(
            [
                (True, {})
            ], orExp.satisfiable(condition)
        )

    def test_and_or_satisfiable_without_condition(self):
        andEx1 = AndExpression(self.fooVar, self.barVar)
        # (foo AND bar) AND (foo OR bar)
        expression = AndExpression(andEx1, OrExpression(self.fooVar, self.barVar))
        self.assertCountEqual(
            [
                (True, {'foo': True, 'bar': True}), (False, {'foo': False}), (False, {'bar': False})
            ], expression.satisfiable({})
        )

    def test_or_duplicate_expression(self):
        expression = OrExpression(OrExpression(self.fooVar, self.barVar), OrExpression(self.fooVar, self.barVar))
        # (foo OR bar) OR (foo OR bar)
        self.assertCountEqual(
            [
                (True, {'foo': True}), (True, {'bar': True}), (False, {'foo': False, 'bar': False})
            ], expression.satisfiable({})
        )
