// Generated from CMake.g4 by ANTLR 4.7.2
import org.antlr.v4.runtime.atn.*;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.misc.*;
import org.antlr.v4.runtime.tree.*;
import java.util.List;
import java.util.Iterator;
import java.util.ArrayList;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast"})
public class CMakeParser extends Parser {
	static { RuntimeMetaData.checkVersion("4.7.2", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		T__0=1, NOT=2, AND=3, IN=4, RANGE=5, VERSION_LESS=6, VERSION_EQUALL=7, 
		VERSION_GREATER=8, STRGREATER=9, STRLESS=10, COMMAND=11, MATCHES=12, WHILE=13, 
		ENDWHILE=14, FUNCTION=15, MACRO=16, ENDFUNCTION=17, ENDMACRO=18, OR=19, 
		IF=20, ELSEIF=21, ELSE=22, ENDIF=23, EXISTS=24, DEFINED=25, TARGET=26, 
		IS_ABSOLUTE=27, IS_DIRECTORY=28, GT=29, GTEQ=30, LT=31, EQ=32, EQR=33, 
		STQE=34, VGEQ=35, POLICY=36, LPAREN=37, RPAREN=38, CONSTANTS=39, Identifier=40, 
		DECIMAL=41, Unquoted_argument=42, Escape_sequence=43, Quoted_argument=44, 
		Bracket_argument=45, Bracket_comment=46, Line_comment=47, Newline=48, 
		Space=49;
	public static final int
		RULE_cmakefile = 0, RULE_commands = 1, RULE_functionCommand = 2, RULE_whileCommand = 3, 
		RULE_whileStatement = 4, RULE_endWhileStatement = 5, RULE_ifCommand = 6, 
		RULE_ifStatement = 7, RULE_elseIfStatement = 8, RULE_elseStatement = 9, 
		RULE_endIfStatement = 10, RULE_functionStatement = 11, RULE_functionBody = 12, 
		RULE_endFunctionStatement = 13, RULE_logical_expr = 14, RULE_optionCommand = 15, 
		RULE_command_invocation = 16, RULE_argument = 17, RULE_constant_value = 18, 
		RULE_single_argument = 19, RULE_compound_argument = 20, RULE_comp_operator = 21;
	private static String[] makeRuleNames() {
		return new String[] {
			"cmakefile", "commands", "functionCommand", "whileCommand", "whileStatement", 
			"endWhileStatement", "ifCommand", "ifStatement", "elseIfStatement", "elseStatement", 
			"endIfStatement", "functionStatement", "functionBody", "endFunctionStatement", 
			"logical_expr", "optionCommand", "command_invocation", "argument", "constant_value", 
			"single_argument", "compound_argument", "comp_operator"
		};
	}
	public static final String[] ruleNames = makeRuleNames();

	private static String[] makeLiteralNames() {
		return new String[] {
			null, "'option'", null, null, null, null, null, null, null, null, null, 
			null, null, null, null, null, null, null, null, null, null, null, null, 
			null, null, null, null, null, null, null, null, null, null, null, null, 
			null, null, "'('", "')'"
		};
	}
	private static final String[] _LITERAL_NAMES = makeLiteralNames();
	private static String[] makeSymbolicNames() {
		return new String[] {
			null, null, "NOT", "AND", "IN", "RANGE", "VERSION_LESS", "VERSION_EQUALL", 
			"VERSION_GREATER", "STRGREATER", "STRLESS", "COMMAND", "MATCHES", "WHILE", 
			"ENDWHILE", "FUNCTION", "MACRO", "ENDFUNCTION", "ENDMACRO", "OR", "IF", 
			"ELSEIF", "ELSE", "ENDIF", "EXISTS", "DEFINED", "TARGET", "IS_ABSOLUTE", 
			"IS_DIRECTORY", "GT", "GTEQ", "LT", "EQ", "EQR", "STQE", "VGEQ", "POLICY", 
			"LPAREN", "RPAREN", "CONSTANTS", "Identifier", "DECIMAL", "Unquoted_argument", 
			"Escape_sequence", "Quoted_argument", "Bracket_argument", "Bracket_comment", 
			"Line_comment", "Newline", "Space"
		};
	}
	private static final String[] _SYMBOLIC_NAMES = makeSymbolicNames();
	public static final Vocabulary VOCABULARY = new VocabularyImpl(_LITERAL_NAMES, _SYMBOLIC_NAMES);

	/**
	 * @deprecated Use {@link #VOCABULARY} instead.
	 */
	@Deprecated
	public static final String[] tokenNames;
	static {
		tokenNames = new String[_SYMBOLIC_NAMES.length];
		for (int i = 0; i < tokenNames.length; i++) {
			tokenNames[i] = VOCABULARY.getLiteralName(i);
			if (tokenNames[i] == null) {
				tokenNames[i] = VOCABULARY.getSymbolicName(i);
			}

			if (tokenNames[i] == null) {
				tokenNames[i] = "<INVALID>";
			}
		}
	}

	@Override
	@Deprecated
	public String[] getTokenNames() {
		return tokenNames;
	}

	@Override

	public Vocabulary getVocabulary() {
		return VOCABULARY;
	}

	@Override
	public String getGrammarFileName() { return "CMake.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public ATN getATN() { return _ATN; }

	public CMakeParser(TokenStream input) {
		super(input);
		_interp = new ParserATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}
	public static class CmakefileContext extends ParserRuleContext {
		public TerminalNode EOF() { return getToken(CMakeParser.EOF, 0); }
		public List<CommandsContext> commands() {
			return getRuleContexts(CommandsContext.class);
		}
		public CommandsContext commands(int i) {
			return getRuleContext(CommandsContext.class,i);
		}
		public CmakefileContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_cmakefile; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterCmakefile(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitCmakefile(this);
		}
	}

	public final CmakefileContext cmakefile() throws RecognitionException {
		CmakefileContext _localctx = new CmakefileContext(_ctx, getState());
		enterRule(_localctx, 0, RULE_cmakefile);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(47);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << WHILE) | (1L << FUNCTION) | (1L << MACRO) | (1L << IF) | (1L << Identifier))) != 0)) {
				{
				{
				setState(44);
				commands();
				}
				}
				setState(49);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(50);
			match(EOF);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class CommandsContext extends ParserRuleContext {
		public FunctionCommandContext functionCommand() {
			return getRuleContext(FunctionCommandContext.class,0);
		}
		public IfCommandContext ifCommand() {
			return getRuleContext(IfCommandContext.class,0);
		}
		public WhileCommandContext whileCommand() {
			return getRuleContext(WhileCommandContext.class,0);
		}
		public OptionCommandContext optionCommand() {
			return getRuleContext(OptionCommandContext.class,0);
		}
		public Command_invocationContext command_invocation() {
			return getRuleContext(Command_invocationContext.class,0);
		}
		public CommandsContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_commands; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterCommands(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitCommands(this);
		}
	}

	public final CommandsContext commands() throws RecognitionException {
		CommandsContext _localctx = new CommandsContext(_ctx, getState());
		enterRule(_localctx, 2, RULE_commands);
		try {
			setState(57);
			_errHandler.sync(this);
			switch (_input.LA(1)) {
			case FUNCTION:
			case MACRO:
				enterOuterAlt(_localctx, 1);
				{
				setState(52);
				functionCommand();
				}
				break;
			case IF:
				enterOuterAlt(_localctx, 2);
				{
				setState(53);
				ifCommand();
				}
				break;
			case WHILE:
				enterOuterAlt(_localctx, 3);
				{
				setState(54);
				whileCommand();
				}
				break;
			case T__0:
				enterOuterAlt(_localctx, 4);
				{
				setState(55);
				optionCommand();
				}
				break;
			case Identifier:
				enterOuterAlt(_localctx, 5);
				{
				setState(56);
				command_invocation();
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class FunctionCommandContext extends ParserRuleContext {
		public FunctionStatementContext functionStatement() {
			return getRuleContext(FunctionStatementContext.class,0);
		}
		public FunctionBodyContext functionBody() {
			return getRuleContext(FunctionBodyContext.class,0);
		}
		public EndFunctionStatementContext endFunctionStatement() {
			return getRuleContext(EndFunctionStatementContext.class,0);
		}
		public FunctionCommandContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_functionCommand; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterFunctionCommand(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitFunctionCommand(this);
		}
	}

	public final FunctionCommandContext functionCommand() throws RecognitionException {
		FunctionCommandContext _localctx = new FunctionCommandContext(_ctx, getState());
		enterRule(_localctx, 4, RULE_functionCommand);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(59);
			functionStatement();
			setState(60);
			functionBody();
			setState(61);
			endFunctionStatement();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class WhileCommandContext extends ParserRuleContext {
		public CommandsContext ifBody;
		public WhileStatementContext whileStatement() {
			return getRuleContext(WhileStatementContext.class,0);
		}
		public EndWhileStatementContext endWhileStatement() {
			return getRuleContext(EndWhileStatementContext.class,0);
		}
		public List<CommandsContext> commands() {
			return getRuleContexts(CommandsContext.class);
		}
		public CommandsContext commands(int i) {
			return getRuleContext(CommandsContext.class,i);
		}
		public WhileCommandContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_whileCommand; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterWhileCommand(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitWhileCommand(this);
		}
	}

	public final WhileCommandContext whileCommand() throws RecognitionException {
		WhileCommandContext _localctx = new WhileCommandContext(_ctx, getState());
		enterRule(_localctx, 6, RULE_whileCommand);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(63);
			whileStatement();
			setState(67);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << WHILE) | (1L << FUNCTION) | (1L << MACRO) | (1L << IF) | (1L << Identifier))) != 0)) {
				{
				{
				setState(64);
				((WhileCommandContext)_localctx).ifBody = commands();
				}
				}
				setState(69);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(70);
			endWhileStatement();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class WhileStatementContext extends ParserRuleContext {
		public TerminalNode WHILE() { return getToken(CMakeParser.WHILE, 0); }
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public WhileStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_whileStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterWhileStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitWhileStatement(this);
		}
	}

	public final WhileStatementContext whileStatement() throws RecognitionException {
		WhileStatementContext _localctx = new WhileStatementContext(_ctx, getState());
		enterRule(_localctx, 8, RULE_whileStatement);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(72);
			match(WHILE);
			setState(73);
			match(LPAREN);
			setState(74);
			logical_expr(0);
			setState(75);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class EndWhileStatementContext extends ParserRuleContext {
		public TerminalNode ENDWHILE() { return getToken(CMakeParser.ENDWHILE, 0); }
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public EndWhileStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_endWhileStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterEndWhileStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitEndWhileStatement(this);
		}
	}

	public final EndWhileStatementContext endWhileStatement() throws RecognitionException {
		EndWhileStatementContext _localctx = new EndWhileStatementContext(_ctx, getState());
		enterRule(_localctx, 10, RULE_endWhileStatement);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(77);
			match(ENDWHILE);
			setState(78);
			match(LPAREN);
			setState(82);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,3,_ctx);
			while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1+1 ) {
					{
					{
					setState(79);
					matchWildcard();
					}
					} 
				}
				setState(84);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,3,_ctx);
			}
			setState(85);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IfCommandContext extends ParserRuleContext {
		public CommandsContext ifBody;
		public CommandsContext elseIfBody;
		public CommandsContext elseBody;
		public IfStatementContext ifStatement() {
			return getRuleContext(IfStatementContext.class,0);
		}
		public EndIfStatementContext endIfStatement() {
			return getRuleContext(EndIfStatementContext.class,0);
		}
		public List<ElseIfStatementContext> elseIfStatement() {
			return getRuleContexts(ElseIfStatementContext.class);
		}
		public ElseIfStatementContext elseIfStatement(int i) {
			return getRuleContext(ElseIfStatementContext.class,i);
		}
		public List<ElseStatementContext> elseStatement() {
			return getRuleContexts(ElseStatementContext.class);
		}
		public ElseStatementContext elseStatement(int i) {
			return getRuleContext(ElseStatementContext.class,i);
		}
		public List<CommandsContext> commands() {
			return getRuleContexts(CommandsContext.class);
		}
		public CommandsContext commands(int i) {
			return getRuleContext(CommandsContext.class,i);
		}
		public IfCommandContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_ifCommand; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterIfCommand(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitIfCommand(this);
		}
	}

	public final IfCommandContext ifCommand() throws RecognitionException {
		IfCommandContext _localctx = new IfCommandContext(_ctx, getState());
		enterRule(_localctx, 12, RULE_ifCommand);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(87);
			ifStatement();
			setState(91);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << WHILE) | (1L << FUNCTION) | (1L << MACRO) | (1L << IF) | (1L << Identifier))) != 0)) {
				{
				{
				setState(88);
				((IfCommandContext)_localctx).ifBody = commands();
				}
				}
				setState(93);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(103);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==ELSEIF) {
				{
				{
				setState(94);
				elseIfStatement();
				setState(98);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << WHILE) | (1L << FUNCTION) | (1L << MACRO) | (1L << IF) | (1L << Identifier))) != 0)) {
					{
					{
					setState(95);
					((IfCommandContext)_localctx).elseIfBody = commands();
					}
					}
					setState(100);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
				}
				setState(105);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(115);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==ELSE) {
				{
				{
				setState(106);
				elseStatement();
				setState(110);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << T__0) | (1L << WHILE) | (1L << FUNCTION) | (1L << MACRO) | (1L << IF) | (1L << Identifier))) != 0)) {
					{
					{
					setState(107);
					((IfCommandContext)_localctx).elseBody = commands();
					}
					}
					setState(112);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
				}
				setState(117);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(118);
			endIfStatement();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class IfStatementContext extends ParserRuleContext {
		public TerminalNode IF() { return getToken(CMakeParser.IF, 0); }
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public IfStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_ifStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterIfStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitIfStatement(this);
		}
	}

	public final IfStatementContext ifStatement() throws RecognitionException {
		IfStatementContext _localctx = new IfStatementContext(_ctx, getState());
		enterRule(_localctx, 14, RULE_ifStatement);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(120);
			match(IF);
			setState(121);
			match(LPAREN);
			setState(122);
			logical_expr(0);
			setState(123);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ElseIfStatementContext extends ParserRuleContext {
		public TerminalNode ELSEIF() { return getToken(CMakeParser.ELSEIF, 0); }
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public ElseIfStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_elseIfStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterElseIfStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitElseIfStatement(this);
		}
	}

	public final ElseIfStatementContext elseIfStatement() throws RecognitionException {
		ElseIfStatementContext _localctx = new ElseIfStatementContext(_ctx, getState());
		enterRule(_localctx, 16, RULE_elseIfStatement);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(125);
			match(ELSEIF);
			setState(126);
			match(LPAREN);
			setState(127);
			logical_expr(0);
			setState(128);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ElseStatementContext extends ParserRuleContext {
		public TerminalNode ELSE() { return getToken(CMakeParser.ELSE, 0); }
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public ElseStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_elseStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterElseStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitElseStatement(this);
		}
	}

	public final ElseStatementContext elseStatement() throws RecognitionException {
		ElseStatementContext _localctx = new ElseStatementContext(_ctx, getState());
		enterRule(_localctx, 18, RULE_elseStatement);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(130);
			match(ELSE);
			setState(131);
			match(LPAREN);
			setState(135);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,9,_ctx);
			while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1+1 ) {
					{
					{
					setState(132);
					matchWildcard();
					}
					} 
				}
				setState(137);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,9,_ctx);
			}
			setState(138);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class EndIfStatementContext extends ParserRuleContext {
		public TerminalNode ENDIF() { return getToken(CMakeParser.ENDIF, 0); }
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public EndIfStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_endIfStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterEndIfStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitEndIfStatement(this);
		}
	}

	public final EndIfStatementContext endIfStatement() throws RecognitionException {
		EndIfStatementContext _localctx = new EndIfStatementContext(_ctx, getState());
		enterRule(_localctx, 20, RULE_endIfStatement);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(140);
			match(ENDIF);
			setState(141);
			match(LPAREN);
			setState(145);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,10,_ctx);
			while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1+1 ) {
					{
					{
					setState(142);
					matchWildcard();
					}
					} 
				}
				setState(147);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,10,_ctx);
			}
			setState(148);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class FunctionStatementContext extends ParserRuleContext {
		public ArgumentContext argument() {
			return getRuleContext(ArgumentContext.class,0);
		}
		public TerminalNode FUNCTION() { return getToken(CMakeParser.FUNCTION, 0); }
		public TerminalNode MACRO() { return getToken(CMakeParser.MACRO, 0); }
		public FunctionStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_functionStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterFunctionStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitFunctionStatement(this);
		}
	}

	public final FunctionStatementContext functionStatement() throws RecognitionException {
		FunctionStatementContext _localctx = new FunctionStatementContext(_ctx, getState());
		enterRule(_localctx, 22, RULE_functionStatement);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(150);
			_la = _input.LA(1);
			if ( !(_la==FUNCTION || _la==MACRO) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			setState(151);
			argument();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class FunctionBodyContext extends ParserRuleContext {
		public Token body;
		public FunctionBodyContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_functionBody; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterFunctionBody(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitFunctionBody(this);
		}
	}

	public final FunctionBodyContext functionBody() throws RecognitionException {
		FunctionBodyContext _localctx = new FunctionBodyContext(_ctx, getState());
		enterRule(_localctx, 24, RULE_functionBody);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			{
			setState(156);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,11,_ctx);
			while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1+1 ) {
					{
					{
					setState(153);
					((FunctionBodyContext)_localctx).body = matchWildcard();
					}
					} 
				}
				setState(158);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,11,_ctx);
			}
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class EndFunctionStatementContext extends ParserRuleContext {
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public TerminalNode ENDFUNCTION() { return getToken(CMakeParser.ENDFUNCTION, 0); }
		public TerminalNode ENDMACRO() { return getToken(CMakeParser.ENDMACRO, 0); }
		public EndFunctionStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_endFunctionStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterEndFunctionStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitEndFunctionStatement(this);
		}
	}

	public final EndFunctionStatementContext endFunctionStatement() throws RecognitionException {
		EndFunctionStatementContext _localctx = new EndFunctionStatementContext(_ctx, getState());
		enterRule(_localctx, 26, RULE_endFunctionStatement);
		int _la;
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(159);
			_la = _input.LA(1);
			if ( !(_la==ENDFUNCTION || _la==ENDMACRO) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			setState(160);
			match(LPAREN);
			setState(164);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,12,_ctx);
			while ( _alt!=1 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1+1 ) {
					{
					{
					setState(161);
					matchWildcard();
					}
					} 
				}
				setState(166);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,12,_ctx);
			}
			setState(167);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class Logical_exprContext extends ParserRuleContext {
		public Logical_exprContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_logical_expr; }
	 
		public Logical_exprContext() { }
		public void copyFrom(Logical_exprContext ctx) {
			super.copyFrom(ctx);
		}
	}
	public static class LogicalExpressionExistsContext extends Logical_exprContext {
		public TerminalNode EXISTS() { return getToken(CMakeParser.EXISTS, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public LogicalExpressionExistsContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionExists(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionExists(this);
		}
	}
	public static class LogicalExpressionTargetContext extends Logical_exprContext {
		public TerminalNode TARGET() { return getToken(CMakeParser.TARGET, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public LogicalExpressionTargetContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionTarget(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionTarget(this);
		}
	}
	public static class LogicalExpressionIsAbsoluteContext extends Logical_exprContext {
		public TerminalNode IS_ABSOLUTE() { return getToken(CMakeParser.IS_ABSOLUTE, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public LogicalExpressionIsAbsoluteContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionIsAbsolute(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionIsAbsolute(this);
		}
	}
	public static class LogicalEntityContext extends Logical_exprContext {
		public Single_argumentContext single_argument() {
			return getRuleContext(Single_argumentContext.class,0);
		}
		public LogicalEntityContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalEntity(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalEntity(this);
		}
	}
	public static class ComparisonExpressionContext extends Logical_exprContext {
		public Single_argumentContext left;
		public Comp_operatorContext operator;
		public Single_argumentContext right;
		public List<Single_argumentContext> single_argument() {
			return getRuleContexts(Single_argumentContext.class);
		}
		public Single_argumentContext single_argument(int i) {
			return getRuleContext(Single_argumentContext.class,i);
		}
		public Comp_operatorContext comp_operator() {
			return getRuleContext(Comp_operatorContext.class,0);
		}
		public ComparisonExpressionContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterComparisonExpression(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitComparisonExpression(this);
		}
	}
	public static class LogicalExpressionInParenContext extends Logical_exprContext {
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public LogicalExpressionInParenContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionInParen(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionInParen(this);
		}
	}
	public static class LogicalExpressionPolicyContext extends Logical_exprContext {
		public TerminalNode POLICY() { return getToken(CMakeParser.POLICY, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public LogicalExpressionPolicyContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionPolicy(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionPolicy(this);
		}
	}
	public static class LogicalExpressionAndContext extends Logical_exprContext {
		public List<Logical_exprContext> logical_expr() {
			return getRuleContexts(Logical_exprContext.class);
		}
		public Logical_exprContext logical_expr(int i) {
			return getRuleContext(Logical_exprContext.class,i);
		}
		public TerminalNode AND() { return getToken(CMakeParser.AND, 0); }
		public LogicalExpressionAndContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionAnd(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionAnd(this);
		}
	}
	public static class ConstantValueContext extends Logical_exprContext {
		public Constant_valueContext constant_value() {
			return getRuleContext(Constant_valueContext.class,0);
		}
		public ConstantValueContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterConstantValue(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitConstantValue(this);
		}
	}
	public static class LogicalExpressionNotContext extends Logical_exprContext {
		public TerminalNode NOT() { return getToken(CMakeParser.NOT, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public LogicalExpressionNotContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionNot(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionNot(this);
		}
	}
	public static class LogicalExpressionOrContext extends Logical_exprContext {
		public List<Logical_exprContext> logical_expr() {
			return getRuleContexts(Logical_exprContext.class);
		}
		public Logical_exprContext logical_expr(int i) {
			return getRuleContext(Logical_exprContext.class,i);
		}
		public TerminalNode OR() { return getToken(CMakeParser.OR, 0); }
		public LogicalExpressionOrContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionOr(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionOr(this);
		}
	}
	public static class LogicalExpressionDefinedContext extends Logical_exprContext {
		public TerminalNode DEFINED() { return getToken(CMakeParser.DEFINED, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public LogicalExpressionDefinedContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionDefined(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionDefined(this);
		}
	}
	public static class LogicalExpressionIsDirectoryContext extends Logical_exprContext {
		public TerminalNode IS_DIRECTORY() { return getToken(CMakeParser.IS_DIRECTORY, 0); }
		public Logical_exprContext logical_expr() {
			return getRuleContext(Logical_exprContext.class,0);
		}
		public TerminalNode COMMAND() { return getToken(CMakeParser.COMMAND, 0); }
		public LogicalExpressionIsDirectoryContext(Logical_exprContext ctx) { copyFrom(ctx); }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterLogicalExpressionIsDirectory(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitLogicalExpressionIsDirectory(this);
		}
	}

	public final Logical_exprContext logical_expr() throws RecognitionException {
		return logical_expr(0);
	}

	private Logical_exprContext logical_expr(int _p) throws RecognitionException {
		ParserRuleContext _parentctx = _ctx;
		int _parentState = getState();
		Logical_exprContext _localctx = new Logical_exprContext(_ctx, _parentState);
		Logical_exprContext _prevctx = _localctx;
		int _startState = 28;
		enterRecursionRule(_localctx, 28, RULE_logical_expr, _p);
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(196);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,13,_ctx) ) {
			case 1:
				{
				_localctx = new LogicalExpressionNotContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;

				setState(170);
				match(NOT);
				setState(171);
				logical_expr(14);
				}
				break;
			case 2:
				{
				_localctx = new LogicalExpressionExistsContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(172);
				match(EXISTS);
				setState(173);
				logical_expr(13);
				}
				break;
			case 3:
				{
				_localctx = new LogicalExpressionPolicyContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(174);
				match(POLICY);
				setState(175);
				logical_expr(12);
				}
				break;
			case 4:
				{
				_localctx = new LogicalExpressionDefinedContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(176);
				match(DEFINED);
				setState(177);
				logical_expr(11);
				}
				break;
			case 5:
				{
				_localctx = new LogicalExpressionTargetContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(178);
				match(TARGET);
				setState(179);
				logical_expr(10);
				}
				break;
			case 6:
				{
				_localctx = new LogicalExpressionIsAbsoluteContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(180);
				match(IS_ABSOLUTE);
				setState(181);
				logical_expr(9);
				}
				break;
			case 7:
				{
				_localctx = new LogicalExpressionIsDirectoryContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(182);
				match(IS_DIRECTORY);
				setState(183);
				logical_expr(8);
				}
				break;
			case 8:
				{
				_localctx = new LogicalExpressionIsDirectoryContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(184);
				match(COMMAND);
				setState(185);
				logical_expr(7);
				}
				break;
			case 9:
				{
				_localctx = new ComparisonExpressionContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(186);
				((ComparisonExpressionContext)_localctx).left = single_argument();
				setState(187);
				((ComparisonExpressionContext)_localctx).operator = comp_operator();
				setState(188);
				((ComparisonExpressionContext)_localctx).right = single_argument();
				}
				break;
			case 10:
				{
				_localctx = new LogicalExpressionInParenContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(190);
				match(LPAREN);
				setState(191);
				logical_expr(0);
				setState(192);
				match(RPAREN);
				}
				break;
			case 11:
				{
				_localctx = new ConstantValueContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(194);
				constant_value();
				}
				break;
			case 12:
				{
				_localctx = new LogicalEntityContext(_localctx);
				_ctx = _localctx;
				_prevctx = _localctx;
				setState(195);
				single_argument();
				}
				break;
			}
			_ctx.stop = _input.LT(-1);
			setState(206);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,15,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					if ( _parseListeners!=null ) triggerExitRuleEvent();
					_prevctx = _localctx;
					{
					setState(204);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,14,_ctx) ) {
					case 1:
						{
						_localctx = new LogicalExpressionAndContext(new Logical_exprContext(_parentctx, _parentState));
						pushNewRecursionContext(_localctx, _startState, RULE_logical_expr);
						setState(198);
						if (!(precpred(_ctx, 6))) throw new FailedPredicateException(this, "precpred(_ctx, 6)");
						setState(199);
						match(AND);
						setState(200);
						logical_expr(7);
						}
						break;
					case 2:
						{
						_localctx = new LogicalExpressionOrContext(new Logical_exprContext(_parentctx, _parentState));
						pushNewRecursionContext(_localctx, _startState, RULE_logical_expr);
						setState(201);
						if (!(precpred(_ctx, 5))) throw new FailedPredicateException(this, "precpred(_ctx, 5)");
						setState(202);
						match(OR);
						setState(203);
						logical_expr(6);
						}
						break;
					}
					} 
				}
				setState(208);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,15,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			unrollRecursionContexts(_parentctx);
		}
		return _localctx;
	}

	public static class OptionCommandContext extends ParserRuleContext {
		public ArgumentContext argument() {
			return getRuleContext(ArgumentContext.class,0);
		}
		public OptionCommandContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_optionCommand; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterOptionCommand(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitOptionCommand(this);
		}
	}

	public final OptionCommandContext optionCommand() throws RecognitionException {
		OptionCommandContext _localctx = new OptionCommandContext(_ctx, getState());
		enterRule(_localctx, 30, RULE_optionCommand);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(209);
			match(T__0);
			setState(210);
			argument();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class Command_invocationContext extends ParserRuleContext {
		public TerminalNode Identifier() { return getToken(CMakeParser.Identifier, 0); }
		public ArgumentContext argument() {
			return getRuleContext(ArgumentContext.class,0);
		}
		public Command_invocationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_command_invocation; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterCommand_invocation(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitCommand_invocation(this);
		}
	}

	public final Command_invocationContext command_invocation() throws RecognitionException {
		Command_invocationContext _localctx = new Command_invocationContext(_ctx, getState());
		enterRule(_localctx, 32, RULE_command_invocation);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(212);
			match(Identifier);
			setState(213);
			argument();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class ArgumentContext extends ParserRuleContext {
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public List<Single_argumentContext> single_argument() {
			return getRuleContexts(Single_argumentContext.class);
		}
		public Single_argumentContext single_argument(int i) {
			return getRuleContext(Single_argumentContext.class,i);
		}
		public List<Compound_argumentContext> compound_argument() {
			return getRuleContexts(Compound_argumentContext.class);
		}
		public Compound_argumentContext compound_argument(int i) {
			return getRuleContext(Compound_argumentContext.class,i);
		}
		public List<Constant_valueContext> constant_value() {
			return getRuleContexts(Constant_valueContext.class);
		}
		public Constant_valueContext constant_value(int i) {
			return getRuleContext(Constant_valueContext.class,i);
		}
		public ArgumentContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_argument; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterArgument(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitArgument(this);
		}
	}

	public final ArgumentContext argument() throws RecognitionException {
		ArgumentContext _localctx = new ArgumentContext(_ctx, getState());
		enterRule(_localctx, 34, RULE_argument);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(215);
			match(LPAREN);
			setState(221);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << AND) | (1L << COMMAND) | (1L << FUNCTION) | (1L << OR) | (1L << EXISTS) | (1L << TARGET) | (1L << EQ) | (1L << POLICY) | (1L << LPAREN) | (1L << CONSTANTS) | (1L << Identifier) | (1L << DECIMAL) | (1L << Unquoted_argument) | (1L << Quoted_argument) | (1L << Bracket_argument))) != 0)) {
				{
				setState(219);
				_errHandler.sync(this);
				switch ( getInterpreter().adaptivePredict(_input,16,_ctx) ) {
				case 1:
					{
					setState(216);
					single_argument();
					}
					break;
				case 2:
					{
					setState(217);
					compound_argument();
					}
					break;
				case 3:
					{
					setState(218);
					constant_value();
					}
					break;
				}
				}
				setState(223);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(224);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class Constant_valueContext extends ParserRuleContext {
		public TerminalNode CONSTANTS() { return getToken(CMakeParser.CONSTANTS, 0); }
		public TerminalNode DECIMAL() { return getToken(CMakeParser.DECIMAL, 0); }
		public Constant_valueContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_constant_value; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterConstant_value(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitConstant_value(this);
		}
	}

	public final Constant_valueContext constant_value() throws RecognitionException {
		Constant_valueContext _localctx = new Constant_valueContext(_ctx, getState());
		enterRule(_localctx, 36, RULE_constant_value);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(226);
			_la = _input.LA(1);
			if ( !(_la==CONSTANTS || _la==DECIMAL) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class Single_argumentContext extends ParserRuleContext {
		public TerminalNode Identifier() { return getToken(CMakeParser.Identifier, 0); }
		public TerminalNode Unquoted_argument() { return getToken(CMakeParser.Unquoted_argument, 0); }
		public TerminalNode Bracket_argument() { return getToken(CMakeParser.Bracket_argument, 0); }
		public TerminalNode Quoted_argument() { return getToken(CMakeParser.Quoted_argument, 0); }
		public TerminalNode DECIMAL() { return getToken(CMakeParser.DECIMAL, 0); }
		public TerminalNode TARGET() { return getToken(CMakeParser.TARGET, 0); }
		public TerminalNode EQ() { return getToken(CMakeParser.EQ, 0); }
		public TerminalNode OR() { return getToken(CMakeParser.OR, 0); }
		public TerminalNode EXISTS() { return getToken(CMakeParser.EXISTS, 0); }
		public TerminalNode AND() { return getToken(CMakeParser.AND, 0); }
		public TerminalNode COMMAND() { return getToken(CMakeParser.COMMAND, 0); }
		public TerminalNode POLICY() { return getToken(CMakeParser.POLICY, 0); }
		public TerminalNode FUNCTION() { return getToken(CMakeParser.FUNCTION, 0); }
		public Single_argumentContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_single_argument; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterSingle_argument(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitSingle_argument(this);
		}
	}

	public final Single_argumentContext single_argument() throws RecognitionException {
		Single_argumentContext _localctx = new Single_argumentContext(_ctx, getState());
		enterRule(_localctx, 38, RULE_single_argument);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(228);
			_la = _input.LA(1);
			if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << AND) | (1L << COMMAND) | (1L << FUNCTION) | (1L << OR) | (1L << EXISTS) | (1L << TARGET) | (1L << EQ) | (1L << POLICY) | (1L << Identifier) | (1L << DECIMAL) | (1L << Unquoted_argument) | (1L << Quoted_argument) | (1L << Bracket_argument))) != 0)) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class Compound_argumentContext extends ParserRuleContext {
		public TerminalNode LPAREN() { return getToken(CMakeParser.LPAREN, 0); }
		public TerminalNode RPAREN() { return getToken(CMakeParser.RPAREN, 0); }
		public List<Single_argumentContext> single_argument() {
			return getRuleContexts(Single_argumentContext.class);
		}
		public Single_argumentContext single_argument(int i) {
			return getRuleContext(Single_argumentContext.class,i);
		}
		public List<Compound_argumentContext> compound_argument() {
			return getRuleContexts(Compound_argumentContext.class);
		}
		public Compound_argumentContext compound_argument(int i) {
			return getRuleContext(Compound_argumentContext.class,i);
		}
		public Compound_argumentContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_compound_argument; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterCompound_argument(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitCompound_argument(this);
		}
	}

	public final Compound_argumentContext compound_argument() throws RecognitionException {
		Compound_argumentContext _localctx = new Compound_argumentContext(_ctx, getState());
		enterRule(_localctx, 40, RULE_compound_argument);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(230);
			match(LPAREN);
			setState(235);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << AND) | (1L << COMMAND) | (1L << FUNCTION) | (1L << OR) | (1L << EXISTS) | (1L << TARGET) | (1L << EQ) | (1L << POLICY) | (1L << LPAREN) | (1L << Identifier) | (1L << DECIMAL) | (1L << Unquoted_argument) | (1L << Quoted_argument) | (1L << Bracket_argument))) != 0)) {
				{
				setState(233);
				_errHandler.sync(this);
				switch (_input.LA(1)) {
				case AND:
				case COMMAND:
				case FUNCTION:
				case OR:
				case EXISTS:
				case TARGET:
				case EQ:
				case POLICY:
				case Identifier:
				case DECIMAL:
				case Unquoted_argument:
				case Quoted_argument:
				case Bracket_argument:
					{
					setState(231);
					single_argument();
					}
					break;
				case LPAREN:
					{
					setState(232);
					compound_argument();
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				}
				setState(237);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(238);
			match(RPAREN);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public static class Comp_operatorContext extends ParserRuleContext {
		public TerminalNode GT() { return getToken(CMakeParser.GT, 0); }
		public TerminalNode GTEQ() { return getToken(CMakeParser.GTEQ, 0); }
		public TerminalNode LT() { return getToken(CMakeParser.LT, 0); }
		public TerminalNode EQ() { return getToken(CMakeParser.EQ, 0); }
		public TerminalNode EQR() { return getToken(CMakeParser.EQR, 0); }
		public TerminalNode VGEQ() { return getToken(CMakeParser.VGEQ, 0); }
		public TerminalNode STQE() { return getToken(CMakeParser.STQE, 0); }
		public TerminalNode STRLESS() { return getToken(CMakeParser.STRLESS, 0); }
		public TerminalNode STRGREATER() { return getToken(CMakeParser.STRGREATER, 0); }
		public TerminalNode VERSION_GREATER() { return getToken(CMakeParser.VERSION_GREATER, 0); }
		public TerminalNode VERSION_EQUALL() { return getToken(CMakeParser.VERSION_EQUALL, 0); }
		public TerminalNode VERSION_LESS() { return getToken(CMakeParser.VERSION_LESS, 0); }
		public TerminalNode MATCHES() { return getToken(CMakeParser.MATCHES, 0); }
		public Comp_operatorContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_comp_operator; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).enterComp_operator(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof CMakeListener ) ((CMakeListener)listener).exitComp_operator(this);
		}
	}

	public final Comp_operatorContext comp_operator() throws RecognitionException {
		Comp_operatorContext _localctx = new Comp_operatorContext(_ctx, getState());
		enterRule(_localctx, 42, RULE_comp_operator);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(240);
			_la = _input.LA(1);
			if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & ((1L << VERSION_LESS) | (1L << VERSION_EQUALL) | (1L << VERSION_GREATER) | (1L << STRGREATER) | (1L << STRLESS) | (1L << MATCHES) | (1L << GT) | (1L << GTEQ) | (1L << LT) | (1L << EQ) | (1L << EQR) | (1L << STQE) | (1L << VGEQ))) != 0)) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public boolean sempred(RuleContext _localctx, int ruleIndex, int predIndex) {
		switch (ruleIndex) {
		case 14:
			return logical_expr_sempred((Logical_exprContext)_localctx, predIndex);
		}
		return true;
	}
	private boolean logical_expr_sempred(Logical_exprContext _localctx, int predIndex) {
		switch (predIndex) {
		case 0:
			return precpred(_ctx, 6);
		case 1:
			return precpred(_ctx, 5);
		}
		return true;
	}

	public static final String _serializedATN =
		"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\63\u00f5\4\2\t\2"+
		"\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13"+
		"\t\13\4\f\t\f\4\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22"+
		"\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\3\2\7\2\60\n\2\f\2"+
		"\16\2\63\13\2\3\2\3\2\3\3\3\3\3\3\3\3\3\3\5\3<\n\3\3\4\3\4\3\4\3\4\3\5"+
		"\3\5\7\5D\n\5\f\5\16\5G\13\5\3\5\3\5\3\6\3\6\3\6\3\6\3\6\3\7\3\7\3\7\7"+
		"\7S\n\7\f\7\16\7V\13\7\3\7\3\7\3\b\3\b\7\b\\\n\b\f\b\16\b_\13\b\3\b\3"+
		"\b\7\bc\n\b\f\b\16\bf\13\b\7\bh\n\b\f\b\16\bk\13\b\3\b\3\b\7\bo\n\b\f"+
		"\b\16\br\13\b\7\bt\n\b\f\b\16\bw\13\b\3\b\3\b\3\t\3\t\3\t\3\t\3\t\3\n"+
		"\3\n\3\n\3\n\3\n\3\13\3\13\3\13\7\13\u0088\n\13\f\13\16\13\u008b\13\13"+
		"\3\13\3\13\3\f\3\f\3\f\7\f\u0092\n\f\f\f\16\f\u0095\13\f\3\f\3\f\3\r\3"+
		"\r\3\r\3\16\7\16\u009d\n\16\f\16\16\16\u00a0\13\16\3\17\3\17\3\17\7\17"+
		"\u00a5\n\17\f\17\16\17\u00a8\13\17\3\17\3\17\3\20\3\20\3\20\3\20\3\20"+
		"\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20"+
		"\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20\5\20\u00c7\n\20\3\20\3\20\3\20"+
		"\3\20\3\20\3\20\7\20\u00cf\n\20\f\20\16\20\u00d2\13\20\3\21\3\21\3\21"+
		"\3\22\3\22\3\22\3\23\3\23\3\23\3\23\7\23\u00de\n\23\f\23\16\23\u00e1\13"+
		"\23\3\23\3\23\3\24\3\24\3\25\3\25\3\26\3\26\3\26\7\26\u00ec\n\26\f\26"+
		"\16\26\u00ef\13\26\3\26\3\26\3\27\3\27\3\27\7T\u0089\u0093\u009e\u00a6"+
		"\3\36\30\2\4\6\b\n\f\16\20\22\24\26\30\32\34\36 \"$&(*,\2\7\3\2\21\22"+
		"\3\2\23\24\4\2))++\f\2\5\5\r\r\21\21\25\25\32\32\34\34\"\"&&*,./\5\2\b"+
		"\f\16\16\37%\2\u0100\2\61\3\2\2\2\4;\3\2\2\2\6=\3\2\2\2\bA\3\2\2\2\nJ"+
		"\3\2\2\2\fO\3\2\2\2\16Y\3\2\2\2\20z\3\2\2\2\22\177\3\2\2\2\24\u0084\3"+
		"\2\2\2\26\u008e\3\2\2\2\30\u0098\3\2\2\2\32\u009e\3\2\2\2\34\u00a1\3\2"+
		"\2\2\36\u00c6\3\2\2\2 \u00d3\3\2\2\2\"\u00d6\3\2\2\2$\u00d9\3\2\2\2&\u00e4"+
		"\3\2\2\2(\u00e6\3\2\2\2*\u00e8\3\2\2\2,\u00f2\3\2\2\2.\60\5\4\3\2/.\3"+
		"\2\2\2\60\63\3\2\2\2\61/\3\2\2\2\61\62\3\2\2\2\62\64\3\2\2\2\63\61\3\2"+
		"\2\2\64\65\7\2\2\3\65\3\3\2\2\2\66<\5\6\4\2\67<\5\16\b\28<\5\b\5\29<\5"+
		" \21\2:<\5\"\22\2;\66\3\2\2\2;\67\3\2\2\2;8\3\2\2\2;9\3\2\2\2;:\3\2\2"+
		"\2<\5\3\2\2\2=>\5\30\r\2>?\5\32\16\2?@\5\34\17\2@\7\3\2\2\2AE\5\n\6\2"+
		"BD\5\4\3\2CB\3\2\2\2DG\3\2\2\2EC\3\2\2\2EF\3\2\2\2FH\3\2\2\2GE\3\2\2\2"+
		"HI\5\f\7\2I\t\3\2\2\2JK\7\17\2\2KL\7\'\2\2LM\5\36\20\2MN\7(\2\2N\13\3"+
		"\2\2\2OP\7\20\2\2PT\7\'\2\2QS\13\2\2\2RQ\3\2\2\2SV\3\2\2\2TU\3\2\2\2T"+
		"R\3\2\2\2UW\3\2\2\2VT\3\2\2\2WX\7(\2\2X\r\3\2\2\2Y]\5\20\t\2Z\\\5\4\3"+
		"\2[Z\3\2\2\2\\_\3\2\2\2][\3\2\2\2]^\3\2\2\2^i\3\2\2\2_]\3\2\2\2`d\5\22"+
		"\n\2ac\5\4\3\2ba\3\2\2\2cf\3\2\2\2db\3\2\2\2de\3\2\2\2eh\3\2\2\2fd\3\2"+
		"\2\2g`\3\2\2\2hk\3\2\2\2ig\3\2\2\2ij\3\2\2\2ju\3\2\2\2ki\3\2\2\2lp\5\24"+
		"\13\2mo\5\4\3\2nm\3\2\2\2or\3\2\2\2pn\3\2\2\2pq\3\2\2\2qt\3\2\2\2rp\3"+
		"\2\2\2sl\3\2\2\2tw\3\2\2\2us\3\2\2\2uv\3\2\2\2vx\3\2\2\2wu\3\2\2\2xy\5"+
		"\26\f\2y\17\3\2\2\2z{\7\26\2\2{|\7\'\2\2|}\5\36\20\2}~\7(\2\2~\21\3\2"+
		"\2\2\177\u0080\7\27\2\2\u0080\u0081\7\'\2\2\u0081\u0082\5\36\20\2\u0082"+
		"\u0083\7(\2\2\u0083\23\3\2\2\2\u0084\u0085\7\30\2\2\u0085\u0089\7\'\2"+
		"\2\u0086\u0088\13\2\2\2\u0087\u0086\3\2\2\2\u0088\u008b\3\2\2\2\u0089"+
		"\u008a\3\2\2\2\u0089\u0087\3\2\2\2\u008a\u008c\3\2\2\2\u008b\u0089\3\2"+
		"\2\2\u008c\u008d\7(\2\2\u008d\25\3\2\2\2\u008e\u008f\7\31\2\2\u008f\u0093"+
		"\7\'\2\2\u0090\u0092\13\2\2\2\u0091\u0090\3\2\2\2\u0092\u0095\3\2\2\2"+
		"\u0093\u0094\3\2\2\2\u0093\u0091\3\2\2\2\u0094\u0096\3\2\2\2\u0095\u0093"+
		"\3\2\2\2\u0096\u0097\7(\2\2\u0097\27\3\2\2\2\u0098\u0099\t\2\2\2\u0099"+
		"\u009a\5$\23\2\u009a\31\3\2\2\2\u009b\u009d\13\2\2\2\u009c\u009b\3\2\2"+
		"\2\u009d\u00a0\3\2\2\2\u009e\u009f\3\2\2\2\u009e\u009c\3\2\2\2\u009f\33"+
		"\3\2\2\2\u00a0\u009e\3\2\2\2\u00a1\u00a2\t\3\2\2\u00a2\u00a6\7\'\2\2\u00a3"+
		"\u00a5\13\2\2\2\u00a4\u00a3\3\2\2\2\u00a5\u00a8\3\2\2\2\u00a6\u00a7\3"+
		"\2\2\2\u00a6\u00a4\3\2\2\2\u00a7\u00a9\3\2\2\2\u00a8\u00a6\3\2\2\2\u00a9"+
		"\u00aa\7(\2\2\u00aa\35\3\2\2\2\u00ab\u00ac\b\20\1\2\u00ac\u00ad\7\4\2"+
		"\2\u00ad\u00c7\5\36\20\20\u00ae\u00af\7\32\2\2\u00af\u00c7\5\36\20\17"+
		"\u00b0\u00b1\7&\2\2\u00b1\u00c7\5\36\20\16\u00b2\u00b3\7\33\2\2\u00b3"+
		"\u00c7\5\36\20\r\u00b4\u00b5\7\34\2\2\u00b5\u00c7\5\36\20\f\u00b6\u00b7"+
		"\7\35\2\2\u00b7\u00c7\5\36\20\13\u00b8\u00b9\7\36\2\2\u00b9\u00c7\5\36"+
		"\20\n\u00ba\u00bb\7\r\2\2\u00bb\u00c7\5\36\20\t\u00bc\u00bd\5(\25\2\u00bd"+
		"\u00be\5,\27\2\u00be\u00bf\5(\25\2\u00bf\u00c7\3\2\2\2\u00c0\u00c1\7\'"+
		"\2\2\u00c1\u00c2\5\36\20\2\u00c2\u00c3\7(\2\2\u00c3\u00c7\3\2\2\2\u00c4"+
		"\u00c7\5&\24\2\u00c5\u00c7\5(\25\2\u00c6\u00ab\3\2\2\2\u00c6\u00ae\3\2"+
		"\2\2\u00c6\u00b0\3\2\2\2\u00c6\u00b2\3\2\2\2\u00c6\u00b4\3\2\2\2\u00c6"+
		"\u00b6\3\2\2\2\u00c6\u00b8\3\2\2\2\u00c6\u00ba\3\2\2\2\u00c6\u00bc\3\2"+
		"\2\2\u00c6\u00c0\3\2\2\2\u00c6\u00c4\3\2\2\2\u00c6\u00c5\3\2\2\2\u00c7"+
		"\u00d0\3\2\2\2\u00c8\u00c9\f\b\2\2\u00c9\u00ca\7\5\2\2\u00ca\u00cf\5\36"+
		"\20\t\u00cb\u00cc\f\7\2\2\u00cc\u00cd\7\25\2\2\u00cd\u00cf\5\36\20\b\u00ce"+
		"\u00c8\3\2\2\2\u00ce\u00cb\3\2\2\2\u00cf\u00d2\3\2\2\2\u00d0\u00ce\3\2"+
		"\2\2\u00d0\u00d1\3\2\2\2\u00d1\37\3\2\2\2\u00d2\u00d0\3\2\2\2\u00d3\u00d4"+
		"\7\3\2\2\u00d4\u00d5\5$\23\2\u00d5!\3\2\2\2\u00d6\u00d7\7*\2\2\u00d7\u00d8"+
		"\5$\23\2\u00d8#\3\2\2\2\u00d9\u00df\7\'\2\2\u00da\u00de\5(\25\2\u00db"+
		"\u00de\5*\26\2\u00dc\u00de\5&\24\2\u00dd\u00da\3\2\2\2\u00dd\u00db\3\2"+
		"\2\2\u00dd\u00dc\3\2\2\2\u00de\u00e1\3\2\2\2\u00df\u00dd\3\2\2\2\u00df"+
		"\u00e0\3\2\2\2\u00e0\u00e2\3\2\2\2\u00e1\u00df\3\2\2\2\u00e2\u00e3\7("+
		"\2\2\u00e3%\3\2\2\2\u00e4\u00e5\t\4\2\2\u00e5\'\3\2\2\2\u00e6\u00e7\t"+
		"\5\2\2\u00e7)\3\2\2\2\u00e8\u00ed\7\'\2\2\u00e9\u00ec\5(\25\2\u00ea\u00ec"+
		"\5*\26\2\u00eb\u00e9\3\2\2\2\u00eb\u00ea\3\2\2\2\u00ec\u00ef\3\2\2\2\u00ed"+
		"\u00eb\3\2\2\2\u00ed\u00ee\3\2\2\2\u00ee\u00f0\3\2\2\2\u00ef\u00ed\3\2"+
		"\2\2\u00f0\u00f1\7(\2\2\u00f1+\3\2\2\2\u00f2\u00f3\t\6\2\2\u00f3-\3\2"+
		"\2\2\26\61;ET]dipu\u0089\u0093\u009e\u00a6\u00c6\u00ce\u00d0\u00dd\u00df"+
		"\u00eb\u00ed";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}