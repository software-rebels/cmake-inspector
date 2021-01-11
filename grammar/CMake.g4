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
commands: ifCommand|optionCommand|command_invocation;

ifCommand
	: ifStatement (ifBody=commands)* (elseIfStatement (elseIfBody=commands)*)* (elseStatement (elseBody=commands)*)? endIfStatement
	;

ifStatement
	: 'if' LPAREN logical_expr RPAREN
	;

elseIfStatement
	: 'elseif' LPAREN logical_expr RPAREN
	;

elseStatement
	: 'else' argument
	;

endIfStatement
	: 'endif' argument
	;

logical_expr
 : NOT logical_expr                                         # LogicalExpressionNot
 | logical_expr AND logical_expr                            # LogicalExpressionAnd
 | logical_expr OR logical_expr                             # LogicalExpressionOr
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

single_argument
	: Identifier | Unquoted_argument | Bracket_argument | Quoted_argument
	;

compound_argument
	: '(' (single_argument|compound_argument)* ')'
	;

comp_operator : GT | LT | EQ | EQR;

NOT : N O T;
AND : A N D;
OR : O R;

GT : G R E A T E R;
LT : L E S S ;
EQ : E Q U A L;
EQR: M A T C H E S;

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