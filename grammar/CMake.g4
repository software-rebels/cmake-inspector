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
commands: ifCommand|setCommand|optionCommand|add_custom_command|add_test_command|
command_invocation;

ifCommand
	: ifStatement (ifBody=commands)* (elseIfStatement (elseIfBody=commands)*)* (elseStatement (elseBody=commands)*)? endIfStatement
	;

ifStatement
	: 'if' argument
	;

elseIfStatement
	: 'elseif' argument 
	;

elseStatement
	: 'else' argument
	;

endIfStatement
	: 'endif' argument
	;

add_test_command
    : 'add_test' '(' Identifier test_name=single_argument Identifier (test_command+=single_argument)+ ')'
    ;
add_custom_command
    : 'add_custom_command' '(' Identifier (output+=single_argument)* Identifier (command+=single_argument)* (otherArg+=add_custom_command_args)* ')'
    ;

add_custom_command_args
    : argType=('MAIN_DEPENDENCY' | 'DEPENDS' | 'BYPRODUCTS') (argValue+=single_argument)+
    ;

setCommand
	: 'set' argument
	;

optionCommand
    : 'option' argument
    ;

command_invocation
	: Identifier argument
	;

argument
	: '(' (single_argument|compound_argument)* ')'
	;

single_argument
	: Identifier | Unquoted_argument | Bracket_argument | Quoted_argument
	;

compound_argument
	: '(' (single_argument|compound_argument)* ')'
	;

Identifier
	: [A-Za-z_][A-Za-z0-9_]*
	;

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