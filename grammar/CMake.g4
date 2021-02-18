/*
Copyright (c) 2018  zbq.
License for use and distribution: Eclipse Public License
CMake language grammar reference:
https://cmake.org/cmake/help/v3.12/manual/cmake-language.7.html
*/

grammar CMake;

cmakefile
	: commands* EOF
	;
commands: ifCommand
          | whileCommand
          | optionCommand
          | foreachCommand
          | command_invocation
          ;

foreachCommand
	: foreachStatement (ifBody=commands)* endForeachStatement
	;

foreachStatement
	: FOREACH LPAREN foreachExpression RPAREN
	;
foreachExpression
    : single_argument (IN|RANGE)? single_argument*
    ;
endForeachStatement
	: ENDFOREACH LPAREN (logical_expr)* RPAREN
	;

whileCommand
	: whileStatement (ifBody=commands)* endWhileStatement
	;

whileStatement
	: WHILE LPAREN logical_expr RPAREN
	;

endWhileStatement
	: ENDWHILE LPAREN .*? RPAREN
	;

ifCommand
	: ifStatement (ifBody=commands)* (elseIfStatement (elseIfBody=commands)*)* (elseStatement (elseBody=commands)*)* endIfStatement
	;

ifStatement
	: IF LPAREN logical_expr RPAREN
	;

elseIfStatement
	: ELSEIF LPAREN (logical_expr)* RPAREN
	;

elseStatement
	: ELSE LPAREN (logical_expr)* RPAREN
	;

endIfStatement
	: ENDIF LPAREN .*? RPAREN
	;

logical_expr
 : NOT logical_expr                                         # LogicalExpressionNot
 | EXISTS logical_expr                                      # LogicalExpressionExists
 | POLICY logical_expr                                      # LogicalExpressionPolicy
 | DEFINED logical_expr                                     # LogicalExpressionDefined
 | TARGET logical_expr                                      # LogicalExpressionTarget
 | IS_ABSOLUTE logical_expr                                 # LogicalExpressionIsAbsolute
 | IS_DIRECTORY logical_expr                                # LogicalExpressionIsDirectory
 | COMMAND logical_expr                                     # LogicalExpressionIsDirectory
 | logical_expr AND logical_expr                            # LogicalExpressionAnd
 | logical_expr OR logical_expr                             # LogicalExpressionOr
 | logical_expr MATCHES logical_expr                        # LogicalExpressionMatches
 | logical_expr VERSION_LESS logical_expr                   # LogicalExpressionVersionLess
 | logical_expr VERSION_EQUALL logical_expr                 # LogicalExpressionVersionEqual
 | logical_expr VERSION_GREATER logical_expr                # LogicalExpressionVersionGreater
 | logical_expr STRGREATER logical_expr                     # LogicalExpressionStrGreater
 | logical_expr STRLESS logical_expr                        # LogicalExpressionStrLess
 | single_argument comp_operator single_argument            # ComparisonExpression
 | LPAREN logical_expr RPAREN                               # LogicalExpressionInParen
 | constant_value                                           # ConstantValue
 | single_argument                                          # LogicalEntity
 ;

optionCommand
    : 'option' argument
    ;

command_invocation
	: Identifier argument
	;

argument
	: '(' (single_argument|compound_argument|constant_value)* ')'
	;


constant_value: CONSTANTS | DECIMAL;

// TODO: Guess it would be better to replace it with logic expression since many function input is logic
single_argument
	: Identifier | Unquoted_argument | Bracket_argument
	| Quoted_argument | DECIMAL | TARGET | EQ | OR | EXISTS
	| AND | COMMAND| POLICY//TODO: fix the placement from Target onward
	;

compound_argument
	: LPAREN (single_argument|compound_argument)* RPAREN
	;

comp_operator : GT | GTEQ | LT | EQ | EQR | VGEQ | STQE;

NOT : N O T;
AND : A N D;
IN: I N;
RANGE: R A N G E;
VERSION_LESS : V E R S I O N '_' L E S S;
VERSION_EQUALL : V E R S I O N '_' E Q U A L;
VERSION_GREATER : V E R S I O N '_' G R E A T E R;
STRGREATER: S T R G R E A T E R;
STRLESS: S T R L E S S;
COMMAND: C O M M A N D;
MATCHES: M A T C H E S;
FOREACH: F O R E A C H;
ENDFOREACH: E N D F O R E A C H;
WHILE: W H I L E;
ENDWHILE: E N D W H I L E;

OR : O R;
IF: I F;
ELSEIF: E L S E I F;
ELSE: E L S E;
ENDIF: E N D I F ;
EXISTS: E X I S T S;
DEFINED: D E F I N E D;
TARGET: T A R G E T;
IS_ABSOLUTE: I S '_' A B S O L U T E;
IS_DIRECTORY: I S '_' D I R E C T O R Y;

GT : G R E A T E R;
GTEQ : G R E A T E R '_' EQ;
LT : L E S S ;
EQ : E Q U A L;
EQR: M A T C H E S;
STQE: S T R E Q U A L;
VGEQ: V E R S I O N UL G R E A T E R UL E Q U A L;
POLICY: P O L I C Y;

LPAREN : '(' ;
RPAREN : ')' ;

CONSTANTS: O N | Y E S | T R U E | Y | O F F | N O | F A L S E | N;

Identifier
	: [A-Za-z_][A-Za-z0-9_]*
	;

DECIMAL : '-'?[0-9]+('.'[0-9]+)? ;

Unquoted_argument
	: (~[ \t\r\n()#"\\] | Escape_sequence)+
	;
Escape_sequence
	: Escape_identity | Escape_encoded | Escape_semicolon
	;
fragment
Escape_identity
	: '\\' ~[A-Za-z0-9;]
	;
fragment
Escape_encoded
	: '\\t' | '\\r' | '\\n'
	;
fragment
Escape_semicolon
	: '\\;'
	;
Quoted_argument
	: '"' (~[\\"] | Escape_sequence | Quoted_cont)* '"'
//    :'"' (~[\\"] | Escape_sequence | Quoted_cont | \$\{(.*?)\} '"'
	;
fragment
Quoted_cont
	: '\\' ('\r' '\n'? | '\n')
	;
Bracket_argument
	: '[' Bracket_arg_nested ']'
	;
fragment
Bracket_arg_nested
	: '=' Bracket_arg_nested '='
	| '[' .*? ']'
	;
// A recommended way to make parser case insensitive
fragment A : [aA]; // match either an 'a' or 'A'
fragment B : [bB];
fragment C : [cC];
fragment D : [dD];
fragment E : [eE];
fragment F : [fF];
fragment G : [gG];
fragment H : [hH];
fragment I : [iI];
fragment J : [jJ];
fragment K : [kK];
fragment L : [lL];
fragment M : [mM];
fragment N : [nN];
fragment O : [oO];
fragment P : [pP];
fragment Q : [qQ];
fragment R : [rR];
fragment S : [sS];
fragment T : [tT];
fragment U : [uU];
fragment V : [vV];
fragment W : [wW];
fragment X : [xX];
fragment Y : [yY];
fragment Z : [zZ];
fragment UL: '_';
Bracket_comment
	: '#[' Bracket_arg_nested ']'
	-> skip
	;
Line_comment
	: '#' (  // #
	  	  | '[' '='*   // #[==
		  | '[' '='* ~('=' | '[' | '\r' | '\n') ~('\r' | '\n')*  // #[==xx
		  | ~('[' | '\r' | '\n') ~('\r' | '\n')*  // #xx
		  ) ('\r' '\n'? | '\n' | EOF)
    -> skip
	;
Newline
	: ('\r' '\n'? | '\n')+
	-> skip
	;
Space
	: [ \t]+
	-> skip
	;