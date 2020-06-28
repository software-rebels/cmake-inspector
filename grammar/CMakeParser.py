# Generated from CMake.g4 by ANTLR 4.7.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\23")
        buf.write("t\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b")
        buf.write("\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16\t")
        buf.write("\16\3\2\7\2\36\n\2\f\2\16\2!\13\2\3\2\3\2\3\3\3\3\3\3")
        buf.write("\3\3\5\3)\n\3\3\4\3\4\7\4-\n\4\f\4\16\4\60\13\4\3\4\3")
        buf.write("\4\7\4\64\n\4\f\4\16\4\67\13\4\7\49\n\4\f\4\16\4<\13\4")
        buf.write("\3\4\3\4\7\4@\n\4\f\4\16\4C\13\4\5\4E\n\4\3\4\3\4\3\5")
        buf.write("\3\5\3\5\3\6\3\6\3\6\3\7\3\7\3\7\3\b\3\b\3\b\3\t\3\t\3")
        buf.write("\t\3\n\3\n\3\n\3\13\3\13\3\13\3\f\3\f\3\f\7\fa\n\f\f\f")
        buf.write("\16\fd\13\f\3\f\3\f\3\r\3\r\3\16\3\16\3\16\7\16m\n\16")
        buf.write("\f\16\16\16p\13\16\3\16\3\16\3\16\2\2\17\2\4\6\b\n\f\16")
        buf.write("\20\22\24\26\30\32\2\3\4\2\13\f\16\17\2s\2\37\3\2\2\2")
        buf.write("\4(\3\2\2\2\6*\3\2\2\2\bH\3\2\2\2\nK\3\2\2\2\fN\3\2\2")
        buf.write("\2\16Q\3\2\2\2\20T\3\2\2\2\22W\3\2\2\2\24Z\3\2\2\2\26")
        buf.write("]\3\2\2\2\30g\3\2\2\2\32i\3\2\2\2\34\36\5\4\3\2\35\34")
        buf.write("\3\2\2\2\36!\3\2\2\2\37\35\3\2\2\2\37 \3\2\2\2 \"\3\2")
        buf.write("\2\2!\37\3\2\2\2\"#\7\2\2\3#\3\3\2\2\2$)\5\6\4\2%)\5\20")
        buf.write("\t\2&)\5\22\n\2\')\5\24\13\2($\3\2\2\2(%\3\2\2\2(&\3\2")
        buf.write("\2\2(\'\3\2\2\2)\5\3\2\2\2*.\5\b\5\2+-\5\4\3\2,+\3\2\2")
        buf.write("\2-\60\3\2\2\2.,\3\2\2\2./\3\2\2\2/:\3\2\2\2\60.\3\2\2")
        buf.write("\2\61\65\5\n\6\2\62\64\5\4\3\2\63\62\3\2\2\2\64\67\3\2")
        buf.write("\2\2\65\63\3\2\2\2\65\66\3\2\2\2\669\3\2\2\2\67\65\3\2")
        buf.write("\2\28\61\3\2\2\29<\3\2\2\2:8\3\2\2\2:;\3\2\2\2;D\3\2\2")
        buf.write("\2<:\3\2\2\2=A\5\f\7\2>@\5\4\3\2?>\3\2\2\2@C\3\2\2\2A")
        buf.write("?\3\2\2\2AB\3\2\2\2BE\3\2\2\2CA\3\2\2\2D=\3\2\2\2DE\3")
        buf.write("\2\2\2EF\3\2\2\2FG\5\16\b\2G\7\3\2\2\2HI\7\3\2\2IJ\5\26")
        buf.write("\f\2J\t\3\2\2\2KL\7\4\2\2LM\5\26\f\2M\13\3\2\2\2NO\7\5")
        buf.write("\2\2OP\5\26\f\2P\r\3\2\2\2QR\7\6\2\2RS\5\26\f\2S\17\3")
        buf.write("\2\2\2TU\7\7\2\2UV\5\26\f\2V\21\3\2\2\2WX\7\b\2\2XY\5")
        buf.write("\26\f\2Y\23\3\2\2\2Z[\7\13\2\2[\\\5\26\f\2\\\25\3\2\2")
        buf.write("\2]b\7\t\2\2^a\5\30\r\2_a\5\32\16\2`^\3\2\2\2`_\3\2\2")
        buf.write("\2ad\3\2\2\2b`\3\2\2\2bc\3\2\2\2ce\3\2\2\2db\3\2\2\2e")
        buf.write("f\7\n\2\2f\27\3\2\2\2gh\t\2\2\2h\31\3\2\2\2in\7\t\2\2")
        buf.write("jm\5\30\r\2km\5\32\16\2lj\3\2\2\2lk\3\2\2\2mp\3\2\2\2")
        buf.write("nl\3\2\2\2no\3\2\2\2oq\3\2\2\2pn\3\2\2\2qr\7\n\2\2r\33")
        buf.write("\3\2\2\2\r\37(.\65:AD`bln")
        return buf.getvalue()


class CMakeParser ( Parser ):

    grammarFileName = "CMake.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'if'", "'elseif'", "'else'", "'endif'", 
                     "'set'", "'option'", "'('", "')'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "Identifier", "Unquoted_argument", "Escape_sequence", 
                      "Quoted_argument", "Bracket_argument", "Bracket_comment", 
                      "Line_comment", "Newline", "Space" ]

    RULE_cmakefile = 0
    RULE_commands = 1
    RULE_ifCommand = 2
    RULE_ifStatement = 3
    RULE_elseIfStatement = 4
    RULE_elseStatement = 5
    RULE_endIfStatement = 6
    RULE_setCommand = 7
    RULE_optionCommand = 8
    RULE_command_invocation = 9
    RULE_argument = 10
    RULE_single_argument = 11
    RULE_compound_argument = 12

    ruleNames =  [ "cmakefile", "commands", "ifCommand", "ifStatement", 
                   "elseIfStatement", "elseStatement", "endIfStatement", 
                   "setCommand", "optionCommand", "command_invocation", 
                   "argument", "single_argument", "compound_argument" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    Identifier=9
    Unquoted_argument=10
    Escape_sequence=11
    Quoted_argument=12
    Bracket_argument=13
    Bracket_comment=14
    Line_comment=15
    Newline=16
    Space=17

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.7.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class CmakefileContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(CMakeParser.EOF, 0)

        def commands(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CMakeParser.CommandsContext)
            else:
                return self.getTypedRuleContext(CMakeParser.CommandsContext,i)


        def getRuleIndex(self):
            return CMakeParser.RULE_cmakefile

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCmakefile" ):
                listener.enterCmakefile(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCmakefile" ):
                listener.exitCmakefile(self)




    def cmakefile(self):

        localctx = CMakeParser.CmakefileContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_cmakefile)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 29
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << CMakeParser.T__0) | (1 << CMakeParser.T__4) | (1 << CMakeParser.T__5) | (1 << CMakeParser.Identifier))) != 0):
                self.state = 26
                self.commands()
                self.state = 31
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 32
            self.match(CMakeParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CommandsContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ifCommand(self):
            return self.getTypedRuleContext(CMakeParser.IfCommandContext,0)


        def setCommand(self):
            return self.getTypedRuleContext(CMakeParser.SetCommandContext,0)


        def optionCommand(self):
            return self.getTypedRuleContext(CMakeParser.OptionCommandContext,0)


        def command_invocation(self):
            return self.getTypedRuleContext(CMakeParser.Command_invocationContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_commands

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCommands" ):
                listener.enterCommands(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCommands" ):
                listener.exitCommands(self)




    def commands(self):

        localctx = CMakeParser.CommandsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_commands)
        try:
            self.state = 38
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [CMakeParser.T__0]:
                self.enterOuterAlt(localctx, 1)
                self.state = 34
                self.ifCommand()
                pass
            elif token in [CMakeParser.T__4]:
                self.enterOuterAlt(localctx, 2)
                self.state = 35
                self.setCommand()
                pass
            elif token in [CMakeParser.T__5]:
                self.enterOuterAlt(localctx, 3)
                self.state = 36
                self.optionCommand()
                pass
            elif token in [CMakeParser.Identifier]:
                self.enterOuterAlt(localctx, 4)
                self.state = 37
                self.command_invocation()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IfCommandContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.ifBody = None # CommandsContext
            self.elseIfBody = None # CommandsContext
            self.elseBody = None # CommandsContext

        def ifStatement(self):
            return self.getTypedRuleContext(CMakeParser.IfStatementContext,0)


        def endIfStatement(self):
            return self.getTypedRuleContext(CMakeParser.EndIfStatementContext,0)


        def elseIfStatement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CMakeParser.ElseIfStatementContext)
            else:
                return self.getTypedRuleContext(CMakeParser.ElseIfStatementContext,i)


        def elseStatement(self):
            return self.getTypedRuleContext(CMakeParser.ElseStatementContext,0)


        def commands(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CMakeParser.CommandsContext)
            else:
                return self.getTypedRuleContext(CMakeParser.CommandsContext,i)


        def getRuleIndex(self):
            return CMakeParser.RULE_ifCommand

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIfCommand" ):
                listener.enterIfCommand(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIfCommand" ):
                listener.exitIfCommand(self)




    def ifCommand(self):

        localctx = CMakeParser.IfCommandContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_ifCommand)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 40
            self.ifStatement()
            self.state = 44
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << CMakeParser.T__0) | (1 << CMakeParser.T__4) | (1 << CMakeParser.T__5) | (1 << CMakeParser.Identifier))) != 0):
                self.state = 41
                localctx.ifBody = self.commands()
                self.state = 46
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 56
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==CMakeParser.T__1:
                self.state = 47
                self.elseIfStatement()
                self.state = 51
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << CMakeParser.T__0) | (1 << CMakeParser.T__4) | (1 << CMakeParser.T__5) | (1 << CMakeParser.Identifier))) != 0):
                    self.state = 48
                    localctx.elseIfBody = self.commands()
                    self.state = 53
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 58
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 66
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==CMakeParser.T__2:
                self.state = 59
                self.elseStatement()
                self.state = 63
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << CMakeParser.T__0) | (1 << CMakeParser.T__4) | (1 << CMakeParser.T__5) | (1 << CMakeParser.Identifier))) != 0):
                    self.state = 60
                    localctx.elseBody = self.commands()
                    self.state = 65
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)



            self.state = 68
            self.endIfStatement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IfStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def argument(self):
            return self.getTypedRuleContext(CMakeParser.ArgumentContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_ifStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIfStatement" ):
                listener.enterIfStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIfStatement" ):
                listener.exitIfStatement(self)




    def ifStatement(self):

        localctx = CMakeParser.IfStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_ifStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 70
            self.match(CMakeParser.T__0)
            self.state = 71
            self.argument()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElseIfStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def argument(self):
            return self.getTypedRuleContext(CMakeParser.ArgumentContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_elseIfStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElseIfStatement" ):
                listener.enterElseIfStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElseIfStatement" ):
                listener.exitElseIfStatement(self)




    def elseIfStatement(self):

        localctx = CMakeParser.ElseIfStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_elseIfStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 73
            self.match(CMakeParser.T__1)
            self.state = 74
            self.argument()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElseStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def argument(self):
            return self.getTypedRuleContext(CMakeParser.ArgumentContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_elseStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElseStatement" ):
                listener.enterElseStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElseStatement" ):
                listener.exitElseStatement(self)




    def elseStatement(self):

        localctx = CMakeParser.ElseStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_elseStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 76
            self.match(CMakeParser.T__2)
            self.state = 77
            self.argument()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EndIfStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def argument(self):
            return self.getTypedRuleContext(CMakeParser.ArgumentContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_endIfStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEndIfStatement" ):
                listener.enterEndIfStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEndIfStatement" ):
                listener.exitEndIfStatement(self)




    def endIfStatement(self):

        localctx = CMakeParser.EndIfStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_endIfStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 79
            self.match(CMakeParser.T__3)
            self.state = 80
            self.argument()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SetCommandContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def argument(self):
            return self.getTypedRuleContext(CMakeParser.ArgumentContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_setCommand

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSetCommand" ):
                listener.enterSetCommand(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSetCommand" ):
                listener.exitSetCommand(self)




    def setCommand(self):

        localctx = CMakeParser.SetCommandContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_setCommand)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 82
            self.match(CMakeParser.T__4)
            self.state = 83
            self.argument()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OptionCommandContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def argument(self):
            return self.getTypedRuleContext(CMakeParser.ArgumentContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_optionCommand

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOptionCommand" ):
                listener.enterOptionCommand(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOptionCommand" ):
                listener.exitOptionCommand(self)




    def optionCommand(self):

        localctx = CMakeParser.OptionCommandContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_optionCommand)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 85
            self.match(CMakeParser.T__5)
            self.state = 86
            self.argument()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Command_invocationContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Identifier(self):
            return self.getToken(CMakeParser.Identifier, 0)

        def argument(self):
            return self.getTypedRuleContext(CMakeParser.ArgumentContext,0)


        def getRuleIndex(self):
            return CMakeParser.RULE_command_invocation

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCommand_invocation" ):
                listener.enterCommand_invocation(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCommand_invocation" ):
                listener.exitCommand_invocation(self)




    def command_invocation(self):

        localctx = CMakeParser.Command_invocationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_command_invocation)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 88
            self.match(CMakeParser.Identifier)
            self.state = 89
            self.argument()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArgumentContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def single_argument(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CMakeParser.Single_argumentContext)
            else:
                return self.getTypedRuleContext(CMakeParser.Single_argumentContext,i)


        def compound_argument(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CMakeParser.Compound_argumentContext)
            else:
                return self.getTypedRuleContext(CMakeParser.Compound_argumentContext,i)


        def getRuleIndex(self):
            return CMakeParser.RULE_argument

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterArgument" ):
                listener.enterArgument(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitArgument" ):
                listener.exitArgument(self)




    def argument(self):

        localctx = CMakeParser.ArgumentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_argument)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 91
            self.match(CMakeParser.T__6)
            self.state = 96
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << CMakeParser.T__6) | (1 << CMakeParser.Identifier) | (1 << CMakeParser.Unquoted_argument) | (1 << CMakeParser.Quoted_argument) | (1 << CMakeParser.Bracket_argument))) != 0):
                self.state = 94
                self._errHandler.sync(self)
                token = self._input.LA(1)
                if token in [CMakeParser.Identifier, CMakeParser.Unquoted_argument, CMakeParser.Quoted_argument, CMakeParser.Bracket_argument]:
                    self.state = 92
                    self.single_argument()
                    pass
                elif token in [CMakeParser.T__6]:
                    self.state = 93
                    self.compound_argument()
                    pass
                else:
                    raise NoViableAltException(self)

                self.state = 98
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 99
            self.match(CMakeParser.T__7)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Single_argumentContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Identifier(self):
            return self.getToken(CMakeParser.Identifier, 0)

        def Unquoted_argument(self):
            return self.getToken(CMakeParser.Unquoted_argument, 0)

        def Bracket_argument(self):
            return self.getToken(CMakeParser.Bracket_argument, 0)

        def Quoted_argument(self):
            return self.getToken(CMakeParser.Quoted_argument, 0)

        def getRuleIndex(self):
            return CMakeParser.RULE_single_argument

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSingle_argument" ):
                listener.enterSingle_argument(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSingle_argument" ):
                listener.exitSingle_argument(self)




    def single_argument(self):

        localctx = CMakeParser.Single_argumentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_single_argument)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 101
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << CMakeParser.Identifier) | (1 << CMakeParser.Unquoted_argument) | (1 << CMakeParser.Quoted_argument) | (1 << CMakeParser.Bracket_argument))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Compound_argumentContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def single_argument(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CMakeParser.Single_argumentContext)
            else:
                return self.getTypedRuleContext(CMakeParser.Single_argumentContext,i)


        def compound_argument(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CMakeParser.Compound_argumentContext)
            else:
                return self.getTypedRuleContext(CMakeParser.Compound_argumentContext,i)


        def getRuleIndex(self):
            return CMakeParser.RULE_compound_argument

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCompound_argument" ):
                listener.enterCompound_argument(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCompound_argument" ):
                listener.exitCompound_argument(self)




    def compound_argument(self):

        localctx = CMakeParser.Compound_argumentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_compound_argument)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 103
            self.match(CMakeParser.T__6)
            self.state = 108
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << CMakeParser.T__6) | (1 << CMakeParser.Identifier) | (1 << CMakeParser.Unquoted_argument) | (1 << CMakeParser.Quoted_argument) | (1 << CMakeParser.Bracket_argument))) != 0):
                self.state = 106
                self._errHandler.sync(self)
                token = self._input.LA(1)
                if token in [CMakeParser.Identifier, CMakeParser.Unquoted_argument, CMakeParser.Quoted_argument, CMakeParser.Bracket_argument]:
                    self.state = 104
                    self.single_argument()
                    pass
                elif token in [CMakeParser.T__6]:
                    self.state = 105
                    self.compound_argument()
                    pass
                else:
                    raise NoViableAltException(self)

                self.state = 110
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 111
            self.match(CMakeParser.T__7)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





