# Generated from CMake.g4 by ANTLR 4.9.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .CMakeParser import CMakeParser
else:
    from CMakeParser import CMakeParser

# This class defines a complete listener for a parse tree produced by CMakeParser.
class CMakeListener(ParseTreeListener):

    # Enter a parse tree produced by CMakeParser#cmakefile.
    def enterCmakefile(self, ctx:CMakeParser.CmakefileContext):
        pass

    # Exit a parse tree produced by CMakeParser#cmakefile.
    def exitCmakefile(self, ctx:CMakeParser.CmakefileContext):
        pass


    # Enter a parse tree produced by CMakeParser#commands.
    def enterCommands(self, ctx:CMakeParser.CommandsContext):
        pass

    # Exit a parse tree produced by CMakeParser#commands.
    def exitCommands(self, ctx:CMakeParser.CommandsContext):
        pass


    # Enter a parse tree produced by CMakeParser#ifCommand.
    def enterIfCommand(self, ctx:CMakeParser.IfCommandContext):
        pass

    # Exit a parse tree produced by CMakeParser#ifCommand.
    def exitIfCommand(self, ctx:CMakeParser.IfCommandContext):
        pass


    # Enter a parse tree produced by CMakeParser#ifStatement.
    def enterIfStatement(self, ctx:CMakeParser.IfStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#ifStatement.
    def exitIfStatement(self, ctx:CMakeParser.IfStatementContext):
        pass


    # Enter a parse tree produced by CMakeParser#elseIfStatement.
    def enterElseIfStatement(self, ctx:CMakeParser.ElseIfStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#elseIfStatement.
    def exitElseIfStatement(self, ctx:CMakeParser.ElseIfStatementContext):
        pass


    # Enter a parse tree produced by CMakeParser#elseStatement.
    def enterElseStatement(self, ctx:CMakeParser.ElseStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#elseStatement.
    def exitElseStatement(self, ctx:CMakeParser.ElseStatementContext):
        pass


    # Enter a parse tree produced by CMakeParser#endIfStatement.
    def enterEndIfStatement(self, ctx:CMakeParser.EndIfStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#endIfStatement.
    def exitEndIfStatement(self, ctx:CMakeParser.EndIfStatementContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalEntity.
    def enterLogicalEntity(self, ctx:CMakeParser.LogicalEntityContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalEntity.
    def exitLogicalEntity(self, ctx:CMakeParser.LogicalEntityContext):
        pass


    # Enter a parse tree produced by CMakeParser#ComparisonExpression.
    def enterComparisonExpression(self, ctx:CMakeParser.ComparisonExpressionContext):
        pass

    # Exit a parse tree produced by CMakeParser#ComparisonExpression.
    def exitComparisonExpression(self, ctx:CMakeParser.ComparisonExpressionContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionInParen.
    def enterLogicalExpressionInParen(self, ctx:CMakeParser.LogicalExpressionInParenContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionInParen.
    def exitLogicalExpressionInParen(self, ctx:CMakeParser.LogicalExpressionInParenContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionAnd.
    def enterLogicalExpressionAnd(self, ctx:CMakeParser.LogicalExpressionAndContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionAnd.
    def exitLogicalExpressionAnd(self, ctx:CMakeParser.LogicalExpressionAndContext):
        pass


    # Enter a parse tree produced by CMakeParser#ConstantValue.
    def enterConstantValue(self, ctx:CMakeParser.ConstantValueContext):
        pass

    # Exit a parse tree produced by CMakeParser#ConstantValue.
    def exitConstantValue(self, ctx:CMakeParser.ConstantValueContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionNot.
    def enterLogicalExpressionNot(self, ctx:CMakeParser.LogicalExpressionNotContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionNot.
    def exitLogicalExpressionNot(self, ctx:CMakeParser.LogicalExpressionNotContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionOr.
    def enterLogicalExpressionOr(self, ctx:CMakeParser.LogicalExpressionOrContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionOr.
    def exitLogicalExpressionOr(self, ctx:CMakeParser.LogicalExpressionOrContext):
        pass


    # Enter a parse tree produced by CMakeParser#optionCommand.
    def enterOptionCommand(self, ctx:CMakeParser.OptionCommandContext):
        pass

    # Exit a parse tree produced by CMakeParser#optionCommand.
    def exitOptionCommand(self, ctx:CMakeParser.OptionCommandContext):
        pass


    # Enter a parse tree produced by CMakeParser#command_invocation.
    def enterCommand_invocation(self, ctx:CMakeParser.Command_invocationContext):
        pass

    # Exit a parse tree produced by CMakeParser#command_invocation.
    def exitCommand_invocation(self, ctx:CMakeParser.Command_invocationContext):
        pass


    # Enter a parse tree produced by CMakeParser#argument.
    def enterArgument(self, ctx:CMakeParser.ArgumentContext):
        pass

    # Exit a parse tree produced by CMakeParser#argument.
    def exitArgument(self, ctx:CMakeParser.ArgumentContext):
        pass


    # Enter a parse tree produced by CMakeParser#constant_value.
    def enterConstant_value(self, ctx:CMakeParser.Constant_valueContext):
        pass

    # Exit a parse tree produced by CMakeParser#constant_value.
    def exitConstant_value(self, ctx:CMakeParser.Constant_valueContext):
        pass


    # Enter a parse tree produced by CMakeParser#single_argument.
    def enterSingle_argument(self, ctx:CMakeParser.Single_argumentContext):
        pass

    # Exit a parse tree produced by CMakeParser#single_argument.
    def exitSingle_argument(self, ctx:CMakeParser.Single_argumentContext):
        pass


    # Enter a parse tree produced by CMakeParser#compound_argument.
    def enterCompound_argument(self, ctx:CMakeParser.Compound_argumentContext):
        pass

    # Exit a parse tree produced by CMakeParser#compound_argument.
    def exitCompound_argument(self, ctx:CMakeParser.Compound_argumentContext):
        pass


    # Enter a parse tree produced by CMakeParser#comp_operator.
    def enterComp_operator(self, ctx:CMakeParser.Comp_operatorContext):
        pass

    # Exit a parse tree produced by CMakeParser#comp_operator.
    def exitComp_operator(self, ctx:CMakeParser.Comp_operatorContext):
        pass



del CMakeParser