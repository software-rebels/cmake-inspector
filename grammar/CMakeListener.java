// Generated from CMake.g4 by ANTLR 4.7.2
import org.antlr.v4.runtime.tree.ParseTreeListener;

/**
 * This interface defines a complete listener for a parse tree produced by
 * {@link CMakeParser}.
 */
public interface CMakeListener extends ParseTreeListener {
	/**
	 * Enter a parse tree produced by {@link CMakeParser#cmakefile}.
	 * @param ctx the parse tree
	 */
	void enterCmakefile(CMakeParser.CmakefileContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#cmakefile}.
	 * @param ctx the parse tree
	 */
	void exitCmakefile(CMakeParser.CmakefileContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#commands}.
	 * @param ctx the parse tree
	 */
	void enterCommands(CMakeParser.CommandsContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#commands}.
	 * @param ctx the parse tree
	 */
	void exitCommands(CMakeParser.CommandsContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#functionCommand}.
	 * @param ctx the parse tree
	 */
	void enterFunctionCommand(CMakeParser.FunctionCommandContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#functionCommand}.
	 * @param ctx the parse tree
	 */
	void exitFunctionCommand(CMakeParser.FunctionCommandContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#whileCommand}.
	 * @param ctx the parse tree
	 */
	void enterWhileCommand(CMakeParser.WhileCommandContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#whileCommand}.
	 * @param ctx the parse tree
	 */
	void exitWhileCommand(CMakeParser.WhileCommandContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#whileStatement}.
	 * @param ctx the parse tree
	 */
	void enterWhileStatement(CMakeParser.WhileStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#whileStatement}.
	 * @param ctx the parse tree
	 */
	void exitWhileStatement(CMakeParser.WhileStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#endWhileStatement}.
	 * @param ctx the parse tree
	 */
	void enterEndWhileStatement(CMakeParser.EndWhileStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#endWhileStatement}.
	 * @param ctx the parse tree
	 */
	void exitEndWhileStatement(CMakeParser.EndWhileStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#ifCommand}.
	 * @param ctx the parse tree
	 */
	void enterIfCommand(CMakeParser.IfCommandContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#ifCommand}.
	 * @param ctx the parse tree
	 */
	void exitIfCommand(CMakeParser.IfCommandContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#ifStatement}.
	 * @param ctx the parse tree
	 */
	void enterIfStatement(CMakeParser.IfStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#ifStatement}.
	 * @param ctx the parse tree
	 */
	void exitIfStatement(CMakeParser.IfStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#elseIfStatement}.
	 * @param ctx the parse tree
	 */
	void enterElseIfStatement(CMakeParser.ElseIfStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#elseIfStatement}.
	 * @param ctx the parse tree
	 */
	void exitElseIfStatement(CMakeParser.ElseIfStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#elseStatement}.
	 * @param ctx the parse tree
	 */
	void enterElseStatement(CMakeParser.ElseStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#elseStatement}.
	 * @param ctx the parse tree
	 */
	void exitElseStatement(CMakeParser.ElseStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#endIfStatement}.
	 * @param ctx the parse tree
	 */
	void enterEndIfStatement(CMakeParser.EndIfStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#endIfStatement}.
	 * @param ctx the parse tree
	 */
	void exitEndIfStatement(CMakeParser.EndIfStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#functionStatement}.
	 * @param ctx the parse tree
	 */
	void enterFunctionStatement(CMakeParser.FunctionStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#functionStatement}.
	 * @param ctx the parse tree
	 */
	void exitFunctionStatement(CMakeParser.FunctionStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#functionBody}.
	 * @param ctx the parse tree
	 */
	void enterFunctionBody(CMakeParser.FunctionBodyContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#functionBody}.
	 * @param ctx the parse tree
	 */
	void exitFunctionBody(CMakeParser.FunctionBodyContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#endFunctionStatement}.
	 * @param ctx the parse tree
	 */
	void enterEndFunctionStatement(CMakeParser.EndFunctionStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#endFunctionStatement}.
	 * @param ctx the parse tree
	 */
	void exitEndFunctionStatement(CMakeParser.EndFunctionStatementContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionExists}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionExists(CMakeParser.LogicalExpressionExistsContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionExists}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionExists(CMakeParser.LogicalExpressionExistsContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionTarget}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionTarget(CMakeParser.LogicalExpressionTargetContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionTarget}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionTarget(CMakeParser.LogicalExpressionTargetContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionIsAbsolute}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionIsAbsolute(CMakeParser.LogicalExpressionIsAbsoluteContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionIsAbsolute}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionIsAbsolute(CMakeParser.LogicalExpressionIsAbsoluteContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalEntity}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalEntity(CMakeParser.LogicalEntityContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalEntity}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalEntity(CMakeParser.LogicalEntityContext ctx);
	/**
	 * Enter a parse tree produced by the {@code ComparisonExpression}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterComparisonExpression(CMakeParser.ComparisonExpressionContext ctx);
	/**
	 * Exit a parse tree produced by the {@code ComparisonExpression}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitComparisonExpression(CMakeParser.ComparisonExpressionContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionInParen}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionInParen(CMakeParser.LogicalExpressionInParenContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionInParen}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionInParen(CMakeParser.LogicalExpressionInParenContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionPolicy}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionPolicy(CMakeParser.LogicalExpressionPolicyContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionPolicy}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionPolicy(CMakeParser.LogicalExpressionPolicyContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionAnd}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionAnd(CMakeParser.LogicalExpressionAndContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionAnd}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionAnd(CMakeParser.LogicalExpressionAndContext ctx);
	/**
	 * Enter a parse tree produced by the {@code ConstantValue}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterConstantValue(CMakeParser.ConstantValueContext ctx);
	/**
	 * Exit a parse tree produced by the {@code ConstantValue}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitConstantValue(CMakeParser.ConstantValueContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionNot}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionNot(CMakeParser.LogicalExpressionNotContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionNot}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionNot(CMakeParser.LogicalExpressionNotContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionOr}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionOr(CMakeParser.LogicalExpressionOrContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionOr}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionOr(CMakeParser.LogicalExpressionOrContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionDefined}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionDefined(CMakeParser.LogicalExpressionDefinedContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionDefined}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionDefined(CMakeParser.LogicalExpressionDefinedContext ctx);
	/**
	 * Enter a parse tree produced by the {@code LogicalExpressionIsDirectory}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void enterLogicalExpressionIsDirectory(CMakeParser.LogicalExpressionIsDirectoryContext ctx);
	/**
	 * Exit a parse tree produced by the {@code LogicalExpressionIsDirectory}
	 * labeled alternative in {@link CMakeParser#logical_expr}.
	 * @param ctx the parse tree
	 */
	void exitLogicalExpressionIsDirectory(CMakeParser.LogicalExpressionIsDirectoryContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#optionCommand}.
	 * @param ctx the parse tree
	 */
	void enterOptionCommand(CMakeParser.OptionCommandContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#optionCommand}.
	 * @param ctx the parse tree
	 */
	void exitOptionCommand(CMakeParser.OptionCommandContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#command_invocation}.
	 * @param ctx the parse tree
	 */
	void enterCommand_invocation(CMakeParser.Command_invocationContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#command_invocation}.
	 * @param ctx the parse tree
	 */
	void exitCommand_invocation(CMakeParser.Command_invocationContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#argument}.
	 * @param ctx the parse tree
	 */
	void enterArgument(CMakeParser.ArgumentContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#argument}.
	 * @param ctx the parse tree
	 */
	void exitArgument(CMakeParser.ArgumentContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#constant_value}.
	 * @param ctx the parse tree
	 */
	void enterConstant_value(CMakeParser.Constant_valueContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#constant_value}.
	 * @param ctx the parse tree
	 */
	void exitConstant_value(CMakeParser.Constant_valueContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#single_argument}.
	 * @param ctx the parse tree
	 */
	void enterSingle_argument(CMakeParser.Single_argumentContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#single_argument}.
	 * @param ctx the parse tree
	 */
	void exitSingle_argument(CMakeParser.Single_argumentContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#compound_argument}.
	 * @param ctx the parse tree
	 */
	void enterCompound_argument(CMakeParser.Compound_argumentContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#compound_argument}.
	 * @param ctx the parse tree
	 */
	void exitCompound_argument(CMakeParser.Compound_argumentContext ctx);
	/**
	 * Enter a parse tree produced by {@link CMakeParser#comp_operator}.
	 * @param ctx the parse tree
	 */
	void enterComp_operator(CMakeParser.Comp_operatorContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#comp_operator}.
	 * @param ctx the parse tree
	 */
	void exitComp_operator(CMakeParser.Comp_operatorContext ctx);
}