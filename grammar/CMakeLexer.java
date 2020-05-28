// Generated from CMake.g4 by ANTLR 4.7.2
import org.antlr.v4.runtime.Lexer;
import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.Token;
import org.antlr.v4.runtime.TokenStream;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.atn.*;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.misc.*;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast"})
public class CMakeLexer extends Lexer {
	static { RuntimeMetaData.checkVersion("4.7.2", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		T__0=1, T__1=2, T__2=3, T__3=4, T__4=5, T__5=6, T__6=7, Identifier=8, 
		Unquoted_argument=9, Escape_sequence=10, Quoted_argument=11, Bracket_argument=12, 
		Bracket_comment=13, Line_comment=14, Newline=15, Space=16;
	public static String[] channelNames = {
		"DEFAULT_TOKEN_CHANNEL", "HIDDEN"
	};

	public static String[] modeNames = {
		"DEFAULT_MODE"
	};

	private static String[] makeRuleNames() {
		return new String[] {
			"T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", "Identifier", 
			"Unquoted_argument", "Escape_sequence", "Escape_identity", "Escape_encoded", 
			"Escape_semicolon", "Quoted_argument", "Quoted_cont", "Bracket_argument", 
			"Bracket_arg_nested", "Bracket_comment", "Line_comment", "Newline", "Space"
		};
	}
	public static final String[] ruleNames = makeRuleNames();

	private static String[] makeLiteralNames() {
		return new String[] {
			null, "'if'", "'elseif'", "'else()'", "'endif'", "'set'", "'('", "')'"
		};
	}
	private static final String[] _LITERAL_NAMES = makeLiteralNames();
	private static String[] makeSymbolicNames() {
		return new String[] {
			null, null, null, null, null, null, null, null, "Identifier", "Unquoted_argument", 
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


	public CMakeLexer(CharStream input) {
		super(input);
		_interp = new LexerATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}

	@Override
	public String getGrammarFileName() { return "CMake.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public String[] getChannelNames() { return channelNames; }

	@Override
	public String[] getModeNames() { return modeNames; }

	@Override
	public ATN getATN() { return _ATN; }

	public static final String _serializedATN =
		"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\22\u00d4\b\1\4\2"+
		"\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4"+
		"\13\t\13\4\f\t\f\4\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22"+
		"\t\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\3\2\3\2\3\2\3\3\3\3\3\3"+
		"\3\3\3\3\3\3\3\3\3\4\3\4\3\4\3\4\3\4\3\4\3\4\3\5\3\5\3\5\3\5\3\5\3\5\3"+
		"\6\3\6\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\7\tO\n\t\f\t\16\tR\13\t\3\n\3\n"+
		"\6\nV\n\n\r\n\16\nW\3\13\3\13\3\13\5\13]\n\13\3\f\3\f\3\f\3\r\3\r\3\r"+
		"\3\r\3\r\3\r\5\rh\n\r\3\16\3\16\3\16\3\17\3\17\3\17\3\17\7\17q\n\17\f"+
		"\17\16\17t\13\17\3\17\3\17\3\20\3\20\3\20\5\20{\n\20\3\20\5\20~\n\20\3"+
		"\21\3\21\3\21\3\21\3\22\3\22\3\22\3\22\3\22\3\22\7\22\u008a\n\22\f\22"+
		"\16\22\u008d\13\22\3\22\5\22\u0090\n\22\3\23\3\23\3\23\3\23\3\23\3\23"+
		"\3\23\3\23\3\24\3\24\3\24\3\24\7\24\u009e\n\24\f\24\16\24\u00a1\13\24"+
		"\3\24\3\24\7\24\u00a5\n\24\f\24\16\24\u00a8\13\24\3\24\3\24\7\24\u00ac"+
		"\n\24\f\24\16\24\u00af\13\24\3\24\3\24\7\24\u00b3\n\24\f\24\16\24\u00b6"+
		"\13\24\5\24\u00b8\n\24\3\24\3\24\5\24\u00bc\n\24\3\24\5\24\u00bf\n\24"+
		"\3\24\3\24\3\25\3\25\5\25\u00c5\n\25\3\25\6\25\u00c8\n\25\r\25\16\25\u00c9"+
		"\3\25\3\25\3\26\6\26\u00cf\n\26\r\26\16\26\u00d0\3\26\3\26\3\u008b\2\27"+
		"\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27\2\31\2\33\2\35\r\37"+
		"\2!\16#\2%\17\'\20)\21+\22\3\2\f\5\2C\\aac|\6\2\62;C\\aac|\b\2\13\f\17"+
		"\17\"\"$%*+^^\6\2\62;==C\\c|\4\2$$^^\6\2\f\f\17\17??]]\4\2\f\f\17\17\5"+
		"\2\f\f\17\17]]\3\3\f\f\4\2\13\13\"\"\2\u00e9\2\3\3\2\2\2\2\5\3\2\2\2\2"+
		"\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2"+
		"\2\2\2\23\3\2\2\2\2\25\3\2\2\2\2\35\3\2\2\2\2!\3\2\2\2\2%\3\2\2\2\2\'"+
		"\3\2\2\2\2)\3\2\2\2\2+\3\2\2\2\3-\3\2\2\2\5\60\3\2\2\2\7\67\3\2\2\2\t"+
		">\3\2\2\2\13D\3\2\2\2\rH\3\2\2\2\17J\3\2\2\2\21L\3\2\2\2\23U\3\2\2\2\25"+
		"\\\3\2\2\2\27^\3\2\2\2\31g\3\2\2\2\33i\3\2\2\2\35l\3\2\2\2\37w\3\2\2\2"+
		"!\177\3\2\2\2#\u008f\3\2\2\2%\u0091\3\2\2\2\'\u0099\3\2\2\2)\u00c7\3\2"+
		"\2\2+\u00ce\3\2\2\2-.\7k\2\2./\7h\2\2/\4\3\2\2\2\60\61\7g\2\2\61\62\7"+
		"n\2\2\62\63\7u\2\2\63\64\7g\2\2\64\65\7k\2\2\65\66\7h\2\2\66\6\3\2\2\2"+
		"\678\7g\2\289\7n\2\29:\7u\2\2:;\7g\2\2;<\7*\2\2<=\7+\2\2=\b\3\2\2\2>?"+
		"\7g\2\2?@\7p\2\2@A\7f\2\2AB\7k\2\2BC\7h\2\2C\n\3\2\2\2DE\7u\2\2EF\7g\2"+
		"\2FG\7v\2\2G\f\3\2\2\2HI\7*\2\2I\16\3\2\2\2JK\7+\2\2K\20\3\2\2\2LP\t\2"+
		"\2\2MO\t\3\2\2NM\3\2\2\2OR\3\2\2\2PN\3\2\2\2PQ\3\2\2\2Q\22\3\2\2\2RP\3"+
		"\2\2\2SV\n\4\2\2TV\5\25\13\2US\3\2\2\2UT\3\2\2\2VW\3\2\2\2WU\3\2\2\2W"+
		"X\3\2\2\2X\24\3\2\2\2Y]\5\27\f\2Z]\5\31\r\2[]\5\33\16\2\\Y\3\2\2\2\\Z"+
		"\3\2\2\2\\[\3\2\2\2]\26\3\2\2\2^_\7^\2\2_`\n\5\2\2`\30\3\2\2\2ab\7^\2"+
		"\2bh\7v\2\2cd\7^\2\2dh\7t\2\2ef\7^\2\2fh\7p\2\2ga\3\2\2\2gc\3\2\2\2ge"+
		"\3\2\2\2h\32\3\2\2\2ij\7^\2\2jk\7=\2\2k\34\3\2\2\2lr\7$\2\2mq\n\6\2\2"+
		"nq\5\25\13\2oq\5\37\20\2pm\3\2\2\2pn\3\2\2\2po\3\2\2\2qt\3\2\2\2rp\3\2"+
		"\2\2rs\3\2\2\2su\3\2\2\2tr\3\2\2\2uv\7$\2\2v\36\3\2\2\2w}\7^\2\2xz\7\17"+
		"\2\2y{\7\f\2\2zy\3\2\2\2z{\3\2\2\2{~\3\2\2\2|~\7\f\2\2}x\3\2\2\2}|\3\2"+
		"\2\2~ \3\2\2\2\177\u0080\7]\2\2\u0080\u0081\5#\22\2\u0081\u0082\7_\2\2"+
		"\u0082\"\3\2\2\2\u0083\u0084\7?\2\2\u0084\u0085\5#\22\2\u0085\u0086\7"+
		"?\2\2\u0086\u0090\3\2\2\2\u0087\u008b\7]\2\2\u0088\u008a\13\2\2\2\u0089"+
		"\u0088\3\2\2\2\u008a\u008d\3\2\2\2\u008b\u008c\3\2\2\2\u008b\u0089\3\2"+
		"\2\2\u008c\u008e\3\2\2\2\u008d\u008b\3\2\2\2\u008e\u0090\7_\2\2\u008f"+
		"\u0083\3\2\2\2\u008f\u0087\3\2\2\2\u0090$\3\2\2\2\u0091\u0092\7%\2\2\u0092"+
		"\u0093\7]\2\2\u0093\u0094\3\2\2\2\u0094\u0095\5#\22\2\u0095\u0096\7_\2"+
		"\2\u0096\u0097\3\2\2\2\u0097\u0098\b\23\2\2\u0098&\3\2\2\2\u0099\u00b7"+
		"\7%\2\2\u009a\u00b8\3\2\2\2\u009b\u009f\7]\2\2\u009c\u009e\7?\2\2\u009d"+
		"\u009c\3\2\2\2\u009e\u00a1\3\2\2\2\u009f\u009d\3\2\2\2\u009f\u00a0\3\2"+
		"\2\2\u00a0\u00b8\3\2\2\2\u00a1\u009f\3\2\2\2\u00a2\u00a6\7]\2\2\u00a3"+
		"\u00a5\7?\2\2\u00a4\u00a3\3\2\2\2\u00a5\u00a8\3\2\2\2\u00a6\u00a4\3\2"+
		"\2\2\u00a6\u00a7\3\2\2\2\u00a7\u00a9\3\2\2\2\u00a8\u00a6\3\2\2\2\u00a9"+
		"\u00ad\n\7\2\2\u00aa\u00ac\n\b\2\2\u00ab\u00aa\3\2\2\2\u00ac\u00af\3\2"+
		"\2\2\u00ad\u00ab\3\2\2\2\u00ad\u00ae\3\2\2\2\u00ae\u00b8\3\2\2\2\u00af"+
		"\u00ad\3\2\2\2\u00b0\u00b4\n\t\2\2\u00b1\u00b3\n\b\2\2\u00b2\u00b1\3\2"+
		"\2\2\u00b3\u00b6\3\2\2\2\u00b4\u00b2\3\2\2\2\u00b4\u00b5\3\2\2\2\u00b5"+
		"\u00b8\3\2\2\2\u00b6\u00b4\3\2\2\2\u00b7\u009a\3\2\2\2\u00b7\u009b\3\2"+
		"\2\2\u00b7\u00a2\3\2\2\2\u00b7\u00b0\3\2\2\2\u00b8\u00be\3\2\2\2\u00b9"+
		"\u00bb\7\17\2\2\u00ba\u00bc\7\f\2\2\u00bb\u00ba\3\2\2\2\u00bb\u00bc\3"+
		"\2\2\2\u00bc\u00bf\3\2\2\2\u00bd\u00bf\t\n\2\2\u00be\u00b9\3\2\2\2\u00be"+
		"\u00bd\3\2\2\2\u00bf\u00c0\3\2\2\2\u00c0\u00c1\b\24\2\2\u00c1(\3\2\2\2"+
		"\u00c2\u00c4\7\17\2\2\u00c3\u00c5\7\f\2\2\u00c4\u00c3\3\2\2\2\u00c4\u00c5"+
		"\3\2\2\2\u00c5\u00c8\3\2\2\2\u00c6\u00c8\7\f\2\2\u00c7\u00c2\3\2\2\2\u00c7"+
		"\u00c6\3\2\2\2\u00c8\u00c9\3\2\2\2\u00c9\u00c7\3\2\2\2\u00c9\u00ca\3\2"+
		"\2\2\u00ca\u00cb\3\2\2\2\u00cb\u00cc\b\25\2\2\u00cc*\3\2\2\2\u00cd\u00cf"+
		"\t\13\2\2\u00ce\u00cd\3\2\2\2\u00cf\u00d0\3\2\2\2\u00d0\u00ce\3\2\2\2"+
		"\u00d0\u00d1\3\2\2\2\u00d1\u00d2\3\2\2\2\u00d2\u00d3\b\26\2\2\u00d3,\3"+
		"\2\2\2\31\2PUW\\gprz}\u008b\u008f\u009f\u00a6\u00ad\u00b4\u00b7\u00bb"+
		"\u00be\u00c4\u00c7\u00c9\u00d0\3\b\2\2";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}