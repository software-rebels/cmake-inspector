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
	 * Enter a parse tree produced by {@link CMakeParser#setCommand}.
	 * @param ctx the parse tree
	 */
	void enterSetCommand(CMakeParser.SetCommandContext ctx);
	/**
	 * Exit a parse tree produced by {@link CMakeParser#setCommand}.
	 * @param ctx the parse tree
	 */
	void exitSetCommand(CMakeParser.SetCommandContext ctx);
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
}