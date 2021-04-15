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


    # Enter a parse tree produced by CMakeParser#functionCommand.
    def enterFunctionCommand(self, ctx:CMakeParser.FunctionCommandContext):
        pass

    # Exit a parse tree produced by CMakeParser#functionCommand.
    def exitFunctionCommand(self, ctx:CMakeParser.FunctionCommandContext):
        pass


    # Enter a parse tree produced by CMakeParser#whileCommand.
    def enterWhileCommand(self, ctx:CMakeParser.WhileCommandContext):
        pass

    # Exit a parse tree produced by CMakeParser#whileCommand.
    def exitWhileCommand(self, ctx:CMakeParser.WhileCommandContext):
        pass


    # Enter a parse tree produced by CMakeParser#whileStatement.
    def enterWhileStatement(self, ctx:CMakeParser.WhileStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#whileStatement.
    def exitWhileStatement(self, ctx:CMakeParser.WhileStatementContext):
        pass


    # Enter a parse tree produced by CMakeParser#endWhileStatement.
    def enterEndWhileStatement(self, ctx:CMakeParser.EndWhileStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#endWhileStatement.
    def exitEndWhileStatement(self, ctx:CMakeParser.EndWhileStatementContext):
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


    # Enter a parse tree produced by CMakeParser#functionStatement.
    def enterFunctionStatement(self, ctx:CMakeParser.FunctionStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#functionStatement.
    def exitFunctionStatement(self, ctx:CMakeParser.FunctionStatementContext):
        pass


    # Enter a parse tree produced by CMakeParser#functionBody.
    def enterFunctionBody(self, ctx:CMakeParser.FunctionBodyContext):
        pass

    # Exit a parse tree produced by CMakeParser#functionBody.
    def exitFunctionBody(self, ctx:CMakeParser.FunctionBodyContext):
        pass


    # Enter a parse tree produced by CMakeParser#endFunctionStatement.
    def enterEndFunctionStatement(self, ctx:CMakeParser.EndFunctionStatementContext):
        pass

    # Exit a parse tree produced by CMakeParser#endFunctionStatement.
    def exitEndFunctionStatement(self, ctx:CMakeParser.EndFunctionStatementContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionExists.
    def enterLogicalExpressionExists(self, ctx:CMakeParser.LogicalExpressionExistsContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionExists.
    def exitLogicalExpressionExists(self, ctx:CMakeParser.LogicalExpressionExistsContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionTarget.
    def enterLogicalExpressionTarget(self, ctx:CMakeParser.LogicalExpressionTargetContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionTarget.
    def exitLogicalExpressionTarget(self, ctx:CMakeParser.LogicalExpressionTargetContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionIsAbsolute.
    def enterLogicalExpressionIsAbsolute(self, ctx:CMakeParser.LogicalExpressionIsAbsoluteContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionIsAbsolute.
    def exitLogicalExpressionIsAbsolute(self, ctx:CMakeParser.LogicalExpressionIsAbsoluteContext):
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


    # Enter a parse tree produced by CMakeParser#LogicalExpressionPolicy.
    def enterLogicalExpressionPolicy(self, ctx:CMakeParser.LogicalExpressionPolicyContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionPolicy.
    def exitLogicalExpressionPolicy(self, ctx:CMakeParser.LogicalExpressionPolicyContext):
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


    # Enter a parse tree produced by CMakeParser#LogicalExpressionDefined.
    def enterLogicalExpressionDefined(self, ctx:CMakeParser.LogicalExpressionDefinedContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionDefined.
    def exitLogicalExpressionDefined(self, ctx:CMakeParser.LogicalExpressionDefinedContext):
        pass


    # Enter a parse tree produced by CMakeParser#LogicalExpressionIsDirectory.
    def enterLogicalExpressionIsDirectory(self, ctx:CMakeParser.LogicalExpressionIsDirectoryContext):
        pass

    # Exit a parse tree produced by CMakeParser#LogicalExpressionIsDirectory.
    def exitLogicalExpressionIsDirectory(self, ctx:CMakeParser.LogicalExpressionIsDirectoryContext):
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