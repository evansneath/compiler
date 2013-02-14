#!/usr/bin/env python3

"""Parser module

Inherits the Scanner module and parses the attached file's tokens as they are
encountered with the target grammar.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    ParsingError: Denotes an an error while parsing the source file.
    Parser: An implementation of a parser for the source language.
"""

from scanner import Scanner


class ParsingError(Exception):
    """ParsingError class

    An exception created for the Parser class. This bubbles errors up to a
    recoverable resync point.

    Attributes:
        expected: The value expected when the Parser encountered an error.
    """
    def __init__(self, expected):
        self.expected = expected
        return

    def __str__(self):
        return repr(self.expected)


class Parser(Scanner):
    """Parser class

    Parses the given source file using the defined language structure.

    Attributes:
        debug: Boolean attribute denoting if successfully parsed tokens should
            be displayed as they are encountered and parsed.

    Methods:
        parse: Parses the given file until a terminal error is encountered or
            the end-of-file token is reached.
    """
    def __init__(self, debug=False):
        super(Parser, self).__init__()

        # Public class attributes
        self.debug = debug

        # Define the current and future token holders
        self.__current = None
        self.__future = None

        return

    def parse(self, src_path):
        """Begin Parsing

        Begins the parse of the inputted source file.

        Arguments:
            src_path: The input source file to parse.

        Returns:
            True on success, False otherwise.
        """
        self.attach_file(src_path)

        # Advance the tokens twice to populate both current and future tokens
        self.__advance_token()
        self.__advance_token()

        # Begin parsing the <program> structure
        try:
            self.__parse_program()
        except ParsingError as e:
            return False

        return True

    def __error(self, expected):
        """Print Parser Error Message (Private)

        Prints a parser error message with details about the expected token
        and the current token being parsed.

        Arguments:
            expected: A string containing the expected token type/value.
        """
        token = self.__current

        print('Error: "{0}", line {1}'.format(self._src_path, token.line))
        print('    Expected {0}, '.format(expected), end='')
        print('encountered \"{0}\" ({1})'.format(token.value, token.type))
        print('    {0}'.format(self._get_line(token.line)))

        # Raise an error and either bubble up to a resync point or fail out
        raise ParsingError(expected)

        return

    def __advance_token(self):
        """Advance Tokens (Private)

        Populates the 'current' token with the 'future' token and populates
        the 'future' token with the next token in the source file.
        """
        self.__current = self.__future

        if self.__future is None or self.__future.type != 'eof':
            self.__future = self.next_token()

        return

    def __check(self, type, value=None, future=False):
        """Check Token (Private)

        Peeks at the token to see if the current token matches the given
        type and value. If it doesn't, don't make a big deal about it.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token. (Default: None)
            future: If True, the future token is checked (Default: False)

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        token = self.__current

        if future:
            token = self.__future

        return token.type == type and (token.value == value or value is None)

    def __accept(self, type, value=None):
        """Accept Token (Private)

        Compares the token to an expected type and value. If it matches, then
        consume the token. If not, don't make a big deal about it.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token. (Default: None)

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        if self.__check(type, value):
            if self.debug:
                print('>>> Consuming:', self.__current)

            self.__advance_token()
            return True

        return False

    def __match(self, type, value=None):
        """Match Token (Private)

        Compares the token to an expected type and value. If it matches, then
        consume the token. If not, then throw an error and panic.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token. (Default: None)

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        # Check the type, if we specified debug, print everything matchd
        if self.__accept(type, value):
            return True

        # Something different than expected was encountered
        if type in ['identifier', 'integer', 'float', 'string']:
            self.__error(type)
        else:
            self.__error('"'+value+'"')

        return False

    def __parse_program(self):
        """<program> (Private)

        Parses the <program> language structure.

            <program> ::=
                <program_header> <program_body>
        """
        self.__parse_program_header()
        self.__parse_program_body()

        return

    def __parse_program_header(self):
        """<program_header> (Private)

        Parses the <program_header> language structure.

            <program_header> ::=
                'program' <identifier> 'is'
        """
        self.__match('keyword', 'program')
        self.__match('identifier')
        self.__match('keyword', 'is')

        return

    def __parse_program_body(self):
        """<program_body> (Private)

        Parses the <program_body> language structure.

            <program_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'program'
        """
        while not self.__accept('keyword', 'begin'):
            self.__parse_declaration()
            self.__match('symbol', ';')

        while not self.__accept('keyword', 'end'):
            self.__parse_statement()
            self.__match('symbol', ';')

        self.__match('keyword', 'program')

        return

    def __parse_declaration(self):
        """<declaration> (Private)

        Parses the <declaration> language structure.

            <declaration> ::=
                [ 'global' ] <procedure_declaration>
                [ 'global' ] <variable_declaration>
        """
        if self.__accept('keyword', 'global'):
            pass

        if self.__first_procedure_declaration():
            self.__parse_procedure_declaration()
        elif self.__first_variable_declaration():
            self.__parse_variable_declaration()
        else:
            self.__error('declaration')

        return

    def __first_variable_declaration(self):
        """first(<variable_declaration>) (Private)

        Determines if current token matches the first terminals.

            first(<variable_declaration>) ::=
                integer | float | bool | string

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return (self.__check('keyword', 'integer') or
                self.__check('keyword', 'float') or
                self.__check('keyword', 'bool') or
                self.__check('keyword', 'string'))

    def __parse_variable_declaration(self):
        """<variable_declaration> (Private)

        Parses the <variable_declaration> language structure.

            <variable_declaration> ::=
                <type_mark> <identifier> [ '[' <array_size> ']' ]
        """
        if self.__accept('keyword', 'integer'):
            pass
        elif self.__accept('keyword', 'float'):
            pass
        elif self.__accept('keyword', 'bool'):
            pass
        elif self.__accept('keyword', 'string'):
            pass
        else:
            self.__error('variable declaration')
            return

        self.__match('identifier')

        if self.__accept('symbol', '['):
            self.__parse_number()
            self.__match('symbol', ']')

        return

    def __first_procedure_declaration(self):
        """first(<procedure_declarations>) (Private)

        Determines if current token matches the first terminals.

            first(<procedure_declaration>) ::=
                'procedure'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.__check('keyword', 'procedure')

    def __parse_procedure_declaration(self):
        """<procedure_declaration> (Private)

        Parses the <procedure_declaration> language structure.

            <procedure_declaration> ::=
                <procedure_header> <procedure_body>
        """
        self.__parse_procedure_header()
        self.__parse_procedure_body()

        return

    def __parse_procedure_header(self):
        """<procedure_header> (Private)

        Parses the <procedure_header> language structure.

            <procedure_header> ::=
                'procedure' <identifier> '(' [ <parameter_list> ] ')'
        """
        self.__match('keyword', 'procedure')
        self.__match('identifier')
        self.__match('symbol', '(')

        if not self.__check('symbol', ')'):
            self.__parse_parameter_list()

        self.__match('symbol', ')')

        return

    def __parse_procedure_body(self):
        """<procedure_body> (Private)

        Parses the <procedure_body> language structure.

            <procedure_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'procedure'
        """
        while not self.__accept('keyword', 'begin'):
            self.__parse_declaration()
            self.__match('symbol', ';')

        while not self.__accept('keyword', 'end'):
            self.__parse_statement()
            self.__match('symbol', ';')

        self.__match('keyword', 'procedure')

        return

    def __parse_parameter_list(self):
        """<parameter_list> (Private)

        Parse the <parameter_list> language structure.

            <parameter_list> ::=
                <parameter> ',' <parameter_list> |
                <parameter>
        """
        self.__parse_parameter()

        if self.__accept('symbol', ','):
            self.__parse_parameter_list()

        return

    def __parse_parameter(self):
        """<parameter> (Private)

        Parse the <parameter> language structure.

            <parameter> ::=
                <variable_declaration> ( 'in' | 'out' )
        """
        self.__parse_variable_declaration()

        if self.__accept('keyword', 'in'):
            pass
        elif self.__accept('keyword', 'out'):
            pass
        else:
            self.__error('\"in\" or \"out\"')

        return

    def __parse_statement(self):
        """<statement> (Private)

        Parse the <statement> language structure.

            <statement> ::=
                <assignment_statement> |
                <if_statement> |
                <loop_statement> |
                <return_statement> |
                <procedure_call>
        """
        if self.__accept('keyword', 'return'):
            pass
        elif self.__first_if_statement():
            self.__parse_if_statement()
        elif self.__first_loop_statement():
            self.__parse_loop_statement()
        elif self.__first_procedure_call():
            self.__parse_procedure_call()
        elif self.__first_assignment_statement():
            self.__parse_assignment_statement()
        else:
            self.__error('statement')

        return

    def __first_assignment_statement(self):
        """first(<assignment_statement>) (Private)

        Determines if current token matches the first terminals.

            first(<assignment_statement>) ::=
                <identifier>

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.__check('identifier')

    def __parse_assignment_statement(self):
        """<assignment_statement> (Private)

        Parses the <assignment_statement> language structure.

            <assignment_statement> ::=
                <destination> ':=' <expression>
        """
        self.__parse_destination()
        self.__match('symbol', ':=')
        self.__parse_expression()

        return

    def __first_if_statement(self):
        """first(<if_statement>) (Private)

        Determines if current token matches the first terminals.

            first(<if_statement>) ::=
                'if'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.__check('keyword', 'if')

    def __parse_if_statement(self):
        """<if_statement> (Private)

        Parses the <if_statement> language structure.

            <if_statement> ::=
                'if' '(' <expression> ')' 'then' ( <statement> ';' )+
                [ 'else' ( <statement> ';' )+ ]
                'end' 'if'
        """
        self.__match('keyword', 'if')
        self.__match('symbol', '(')

        self.__parse_expression()

        self.__match('symbol', ')')
        self.__match('keyword', 'then')

        while True:
            self.__parse_statement()
            self.__match('symbol', ';')

            if (self.__check('keyword', 'else') or
                    self.__check('keyword', 'end')):
                break

        if self.__accept('keyword', 'else'):
            while True:
                self.__parse_statement()
                self.__match('symbol', ';')

                if self.__check('keyword', 'end'):
                    break

        self.__match('keyword', 'end')
        self.__match('keyword', 'if')

        return

    def __first_loop_statement(self):
        """first(<loop_statement>) (Private)

        Determines if current token matches the first terminals.

            first(<loop_statement>) ::=
                'for'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.__check('keyword', 'for')

    def __parse_loop_statement(self):
        """<loop_statement> (Private)

        Parses the <loop_statement> language structure.

            <loop_statement> ::=
                'for' '(' <assignment_statement> ';' <expression> ')'
                    ( <statement> ';' )*
                'end' 'for'
        """
        self.__match('keyword', 'for')
        self.__match('symbol', '(')
        self.__parse_assignment_statement()
        self.__match('symbol', ';')
        self.__parse_expression()
        self.__match('symbol', ')')

        while not self.__accept('keyword', 'end'):
            self.__parse_statement()
            self.__match('symbol', ';')

        self.__match('keyword', 'for')

        return

    def __first_procedure_call(self):
        """first(<procedure_call>) (Private)

        Determines if current token matches the first terminals. The second
        terminal is checked using the future token in this case to distinguish
        the first(<procedure_call>) from first(<assignment_statement>).

            first(<procedure_call>) ::=
                '('

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.__check('symbol', '(', future=True)

    def __parse_procedure_call(self):
        """<procedure_call> (Private)

        Parses the <procedure_call> language structure.

            <procedure_call> ::=
                <identifier> '(' [ <argument_list> ] ')'
        """
        self.__match('identifier')
        self.__match('symbol', '(')

        if not self.__check('symbol', ')'):
            self.__parse_argument_list()

        self.__match('symbol', ')')

        return

    def __parse_argument_list(self):
        """<argument_list> (Private)

        Parses <argument_list> language structure.

            <argument_list> ::=
                <expression> ',' <argument_list> |
                <expression>
        """
        self.__parse_expression()

        if self.__accept('symbol', ','):
            self.__parse_argument_list()

        return

    def __parse_destination(self):
        """<destination> (Private)

        Parses the <destination> language structure.

            <destination> ::=
                <identifier> [ '[' <expression> ']' ]
        """
        self.__match('identifier')

        if self.__accept('symbol', '['):
            self.__parse_expression()
            self.__accept('symbol', ']')

        return

    def __parse_expression(self):
        """<expression> (Private)

        Parses <expression> language structure.

            <expression> ::=
                <expression> '&' <arith_op> |
                <expression> '|' <arith_op> |
                [ 'not' ] <arith_op>
        """
        if self.__accept('keyword', 'not'):
            pass

        self.__parse_arith_op()

        while True:
            if self.__accept('symbol', '&'):
                self.__parse_arith_op()
            elif self.__accept('symbol', '|'):
                self.__parse_arith_op()
            else:
                break

        return

    def __parse_arith_op(self):
        """<arith_op> (Private)

        Parses <arith_op> language structure.

            <arith_op> ::=
                <arith_op> '+' <relation> |
                <arith_op> '-' <relation> |
                <relation>
        """
        self.__parse_relation()

        while True:
            if self.__accept('symbol', '+'):
                self.__parse_relation()
            elif self.__accept('symbol', '-'):
                self.__parse_relation()
            else:
                break

        return

    def __parse_relation(self):
        """<relation> (Private)

        Parses <relation> language structure.

            <relation> ::=
                <relation> '<' <term> |
                <relation> '>' <term> |
                <relation> '>=' <term> |
                <relation> '<=' <term> |
                <relation> '==' <term> |
                <relation> '!=' <term> |
                <term>
        """
        self.__parse_term()

        while True:
            if self.__accept('symbol', '<'):
                self.__parse_term()
            elif self.__accept('symbol', '>'):
                self.__parse_term()
            elif self.__accept('symbol', '<='):
                self.__parse_term()
            elif self.__accept('symbol', '>='):
                self.__parse_term()
            elif self.__accept('symbol', '=='):
                self.__parse_term()
            elif self.__accept('symbol', '!='):
                self.__parse_term()
            else:
                break

        return

    def __parse_term(self):
        """<term> (Private)

        Parses <term> language structure.

            <term> ::=
                <term> '*' <factor> |
                <term> '/' <factor> |
                <factor>
        """
        self.__parse_factor()

        while True:
            if self.__accept('symbol', '*'):
                self.__parse_factor()
            elif self.__accept('symbol', '/'):
                self.__parse_factor()
            else:
                break

        return

    def __parse_factor(self):
        """<factor> (Private)

        Parses <factor> language structure.

            <factor> ::=
                '(' <expression> ')' |
                [ '-' ] <name> |
                [ '-' ] <number> |
                <string> |
                'true' |
                'false'
        """
        if self.__accept('symbol', '('):
            self.__parse_expression()
            self.__match('symbol', ')')
        elif self.__accept('string'):
            pass
        elif self.__accept('keyword', 'true'):
            pass
        elif self.__accept('keyword', 'false'):
            pass
        elif self.__accept('symbol', '-'):
            if self.__first_name():
                self.__parse_name()
            elif self.__check('integer') or self.__check('float'):
                self.__parse_number()
            else:
                self.__error('name or number')
        elif self.__first_name():
            self.__parse_name()
        elif self.__check('integer') or self.__check('float'):
            self.__parse_number()
        else:
            self.__error('factor')

        return

    def __first_name(self):
        """first(<name>) (Private)

        Determines if current token matches the first terminals.

            first(<name>) ::=
                <identifier>

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.__check('identifier')

    def __parse_name(self):
        """<name> (Private)

        Parses <name> language structure.

            <name> ::=
                <identifier> [ '[' <expression> ']' ]
        """
        self.__match('identifier')

        if self.__accept('symbol', '['):
            self.__parse_expression()
            self.__match('symbol', ']')

        return

    def __parse_number(self):
        """Parse Number (Private)

        Parses the <number> language structure.

            <number> ::=
                [0-9][0-9_]*[.[0-9_]*]
        """
        if self.__accept('integer'):
            pass
        elif self.__accept('float'):
            pass
        else:
            self.__error('number')

        return
