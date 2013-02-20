#!/usr/bin/env python3

"""Parser module

Inherits the Scanner module and parses the attached file's tokens as they are
encountered with the target grammar.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    Parser: An implementation of a parser for the source language.
"""

from scanner import Scanner
from pprint import pprint


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
        self._current = None
        self._future = None

        self._identifiers = [{}]
        self._scope = 0

        return

    def parse(self, src_path):
        """Begin Parsing

        Begins the parse of the inputted source file.

        Arguments:
            src_path: The input source file to parse.

        Returns:
            True on success, False otherwise.
        """
        if not self.attach_file(src_path):
            return False

        # Advance the tokens twice to populate both current and future tokens
        self._advance_token()
        self._advance_token()

        # Begin parsing the root <program> language structure
        try:
            self._parse_program()
        except SyntaxError:
            return False

        # Make sure there's no junk after the end of program
        if not self._check('eof'):
            self._warning('eof')

        return True

    def _warning(self, expected, prefix='Warning'):
        """Print Parser Warning Message (Protected)

        Prints a parser warning message with details about the expected token
        and the current token being parsed.

        Arguments:
            expected: A string containing the expected token type/value.
            prefix: A string value to be printed at the start of the warning.
                Overwritten for error messages. (Default: 'Warning')
        """
        token = self._current

        print('{0}: "{1}", line {2}'.format(prefix, self._src_path, token.line))
        print('    Expected {0}, '.format(expected), end='')
        print('encountered "{0}" ({1})'.format(token.value, token.type))
        print('    {0}'.format(self._get_line(token.line)))

        return

    def _error(self, expected):
        """Print Parser Error Message (Protected)

        Prints a parser error message with details about the expected token
        and the current token being parsed. After error printing, an exception
        is raised to be caught and resolved by parent nodes.

        Arguments:
            expected: A string containing the expected token type/value.

        Raises:
            SyntaxError: If this method is being called, an error has been
                encountered during parsing.
        """
        self._warning(expected, prefix='Error')
        raise SyntaxError()

        return

    def _push_scope(self):
        """Push New Identifier Scope (Protected)

        Creates a new scope on the identifiers table and increases the global
        current scope counter.
        """
        self._scope += 1
        self._identifiers.append({})

        if self.debug:
            print('Pushing new scope:', self._scope)
            pprint(self._identifiers)

        return

    def _pop_scope(self):
        """Pop Highest Identifier Scope (Protected)

        Disposes of the current scope in the identifiers table and decrements
        the global current scope counter.
        """
        if self.debug:
            print('Popping scope:', self._scope)
            pprint(self._identifiers)

        self._identifiers.pop(self._scope)
        self._scope -= 1

        return

    def _advance_token(self):
        """Advance Tokens (Protected)

        Populates the 'current' token with the 'future' token and populates
        the 'future' token with the next token in the source file.
        """
        self._current = self._future

        if self._future is None or self._future.type != 'eof':
            self._future = self.next_token()

        return

    def _check(self, type, value=None, future=False):
        """Check Token (Protected)

        Peeks at the token to see if the current token matches the given
        type and value. If it doesn't, don't make a big deal about it.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token. (Default: None)
            future: If True, the future token is checked (Default: False)

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        token = self._current

        if future:
            token = self._future

        return token.type == type and (token.value == value or value is None)

    def _accept(self, type, value=None):
        """Accept Token (Protected)

        Compares the token to an expected type and value. If it matches, then
        consume the token. If not, don't make a big deal about it.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token. (Default: None)

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        if self._check(type, value):
            if self.debug:
                print('>>> Consuming:', self._current)

            self._advance_token()
            return True

        return False

    def _match(self, type, value=None):
        """Match Token (Protected)

        Compares the token to an expected type and value. If it matches, then
        consume the token. If not, then throw an error and panic.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token. (Default: None)

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        # Check the type, if we specified debug, print everything matchd
        if self._accept(type, value):
            return True

        # Something different than expected was encountered
        if value is not None:
            self._error('"'+value+'" ('+type+')')
        else:
            self._error(type)

        return False

    def _resync_at_token(self, type, value=None):
        """Resync at Token

        Finds the next token of the given type and value and moves the
        current token to that point. Code parsing can continue from there.

        Arguments:
            type: The type of the token to resync.
            value: The value of the token to resync. (Default: None)
        """
        while not self._check(type, value):
            self._advance_token()

        return

    def _parse_program(self):
        """<program> (Protected)

        Parses the <program> language structure.

            <program> ::=
                <program_header> <program_body>
        """
        self._parse_program_header()
        self._parse_program_body()

        return

    def _parse_program_header(self):
        """<program_header> (Protected)

        Parses the <program_header> language structure.

            <program_header> ::=
                'program' <identifier> 'is'
        """
        self._match('keyword', 'program')

        id_name = self._current.value
        self._match('identifier')

        self._match('keyword', 'is')

        self._identifiers[self._scope][id_name] = ('program', None)
        self._push_scope()

        return

    def _parse_program_body(self):
        """<program_body> (Protected)

        Parses the <program_body> language structure.

            <program_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'program'
        """
        while not self._accept('keyword', 'begin'):
            try:
                self._parse_declaration()
            except SyntaxError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except SyntaxError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'program')

        self._pop_scope()

        return

    def _parse_declaration(self):
        """<declaration> (Protected)

        Parses the <declaration> language structure.

            <declaration> ::=
                [ 'global' ] <procedure_declaration>
                [ 'global' ] <variable_declaration>
        """
        is_global = False

        if self._accept('keyword', 'global'):
            is_global = True

        if self._first_procedure_declaration():
            self._parse_procedure_declaration(is_global)
        elif self._first_variable_declaration():
            self._parse_variable_declaration(is_global)
        else:
            self._error('procedure or variable declaration')

        return

    def _first_variable_declaration(self):
        """first(<variable_declaration>) (Protected)

        Determines if current token matches the first terminals.

            first(<variable_declaration>) ::=
                integer | float | bool | string

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return (self._check('keyword', 'integer') or
                self._check('keyword', 'float') or
                self._check('keyword', 'bool') or
                self._check('keyword', 'string'))

    def _parse_variable_declaration(self, is_global=False):
        """<variable_declaration> (Protected)

        Parses the <variable_declaration> language structure.

            <variable_declaration> ::=
                <type_mark> <identifier> [ '[' <array_size> ']' ]

        Arguments:
            is_global: Denotes if the variable is to be globally scoped.
                (Default: False)
        """
        id_scope = self._scope

        if is_global:
            id_scope = 0

        id_type = self._current.value

        if self._accept('keyword', 'integer'):
            pass
        elif self._accept('keyword', 'float'):
            pass
        elif self._accept('keyword', 'bool'):
            pass
        elif self._accept('keyword', 'string'):
            pass
        else:
            self._error('variable declaration')
            return

        id_name = self._current.value
        self._match('identifier')

        id_elements = 1

        if self._accept('symbol', '['):
            # TODO: Throw TypeError if id_element type != integer
            id_elements = self._current.value

            self._parse_number()
            self._match('symbol', ']')

        # The declaration was valid, add the identifier to the table
        self._identifiers[id_scope][id_name] = (id_type, id_elements)

        return

    def _first_procedure_declaration(self):
        """first(<procedure_declarations>) (Protected)

        Determines if current token matches the first terminals.

            first(<procedure_declaration>) ::=
                'procedure'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self._check('keyword', 'procedure')

    def _parse_procedure_declaration(self, is_global):
        """<procedure_declaration> (Protected)

        Parses the <procedure_declaration> language structure.

            <procedure_declaration> ::=
                <procedure_header> <procedure_body>

        Arguments:
            is_global: Denotes if the procedure is to be globally scoped.
        """
        self._parse_procedure_header(is_global)
        self._parse_procedure_body()

        return

    def _parse_procedure_header(self, is_global):
        """<procedure_header> (Protected)

        Parses the <procedure_header> language structure.

            <procedure_header> ::=
                'procedure' <identifier> '(' [ <parameter_list> ] ')'

        Arguments:
            is_global: Denotes if the procedure is to be globally scoped.
        """
        id_scope = self._scope

        if is_global:
            id_scope = 0

        self._match('keyword', 'procedure')

        id_name = self._current.value

        self._match('identifier')
        self._match('symbol', '(')

        if not self._check('symbol', ')'):
            self._parse_parameter_list()

        self._match('symbol', ')')

        # Add the procedure identifier to the parent and its own table
        self._identifiers[id_scope][id_name] = ('procedure', None)
        self._push_scope()
        self._identifiers[self._scope][id_name] = ('procedure', None)

        return

    def _parse_procedure_body(self):
        """<procedure_body> (Protected)

        Parses the <procedure_body> language structure.

            <procedure_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'procedure'
        """
        while not self._accept('keyword', 'begin'):
            try:
                self._parse_declaration()
            except SyntaxError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except SyntaxError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'procedure')

        self._pop_scope()

        return

    def _parse_parameter_list(self):
        """<parameter_list> (Protected)

        Parse the <parameter_list> language structure.

            <parameter_list> ::=
                <parameter> ',' <parameter_list> |
                <parameter>
        """
        self._parse_parameter()

        if self._accept('symbol', ','):
            self._parse_parameter_list()

        return

    def _parse_parameter(self):
        """<parameter> (Protected)

        Parse the <parameter> language structure.

            <parameter> ::=
                <variable_declaration> ( 'in' | 'out' )
        """
        self._parse_variable_declaration()

        if self._accept('keyword', 'in'):
            pass
        elif self._accept('keyword', 'out'):
            pass
        else:
            self._error('"in" or "out"')

        return

    def _parse_statement(self):
        """<statement> (Protected)

        Parse the <statement> language structure.

            <statement> ::=
                <assignment_statement> |
                <if_statement> |
                <loop_statement> |
                <return_statement> |
                <procedure_call>
        """
        if self._accept('keyword', 'return'):
            pass
        elif self._first_if_statement():
            self._parse_if_statement()
        elif self._first_loop_statement():
            self._parse_loop_statement()
        elif self._first_procedure_call():
            self._parse_procedure_call()
        elif self._first_assignment_statement():
            self._parse_assignment_statement()
        else:
            self._error('statement')

        return

    def _first_assignment_statement(self):
        """first(<assignment_statement>) (Protected)

        Determines if current token matches the first terminals.

            first(<assignment_statement>) ::=
                <identifier>

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self._check('identifier')

    def _parse_assignment_statement(self):
        """<assignment_statement> (Protected)

        Parses the <assignment_statement> language structure.

            <assignment_statement> ::=
                <destination> ':=' <expression>
        """
        self._parse_destination()
        self._match('symbol', ':=')
        self._parse_expression()

        return

    def _first_if_statement(self):
        """first(<if_statement>) (Protected)

        Determines if current token matches the first terminals.

            first(<if_statement>) ::=
                'if'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self._check('keyword', 'if')

    def _parse_if_statement(self):
        """<if_statement> (Protected)

        Parses the <if_statement> language structure.

            <if_statement> ::=
                'if' '(' <expression> ')' 'then' ( <statement> ';' )+
                [ 'else' ( <statement> ';' )+ ]
                'end' 'if'
        """
        self._match('keyword', 'if')
        self._match('symbol', '(')
        self._parse_expression()
        self._match('symbol', ')')
        self._match('keyword', 'then')

        while True:
            try:
                self._parse_statement()
            except SyntaxError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

            if self._check('keyword', 'else') or self._check('keyword', 'end'):
                break

        if self._accept('keyword', 'else'):
            while True:
                try:
                    self._parse_statement()
                except SyntaxError:
                    self._resync_at_token('symbol', ';')

                self._match('symbol', ';')

                if self._check('keyword', 'end'):
                    break

        self._match('keyword', 'end')
        self._match('keyword', 'if')

        return

    def _first_loop_statement(self):
        """first(<loop_statement>) (Protected)

        Determines if current token matches the first terminals.

            first(<loop_statement>) ::=
                'for'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self._check('keyword', 'for')

    def _parse_loop_statement(self):
        """<loop_statement> (Protected)

        Parses the <loop_statement> language structure.

            <loop_statement> ::=
                'for' '(' <assignment_statement> ';' <expression> ')'
                    ( <statement> ';' )*
                'end' 'for'
        """
        self._match('keyword', 'for')
        self._match('symbol', '(')

        try:
            self._parse_assignment_statement()
        except SyntaxError:
            self._resync_at_token('symbol', ';')

        self._match('symbol', ';')
        self._parse_expression()
        self._match('symbol', ')')

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except SyntaxError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'for')

        return

    def _first_procedure_call(self):
        """first(<procedure_call>) (Protected)

        Determines if current token matches the first terminals. The second
        terminal is checked using the future token in this case to distinguish
        the first(<procedure_call>) from first(<assignment_statement>).

            first(<procedure_call>) ::=
                '('

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self._check('symbol', '(', future=True)

    def _parse_procedure_call(self):
        """<procedure_call> (Protected)

        Parses the <procedure_call> language structure.

            <procedure_call> ::=
                <identifier> '(' [ <argument_list> ] ')'
        """
        self._match('identifier')
        self._match('symbol', '(')

        if not self._check('symbol', ')'):
            self._parse_argument_list()

        self._match('symbol', ')')

        return

    def _parse_argument_list(self):
        """<argument_list> (Protected)

        Parses <argument_list> language structure.

            <argument_list> ::=
                <expression> ',' <argument_list> |
                <expression>
        """
        self._parse_expression()

        if self._accept('symbol', ','):
            self._parse_argument_list()

        return

    def _parse_destination(self):
        """<destination> (Protected)

        Parses the <destination> language structure.

            <destination> ::=
                <identifier> [ '[' <expression> ']' ]
        """
        self._match('identifier')

        if self._accept('symbol', '['):
            self._parse_expression()
            self._accept('symbol', ']')

        return

    def _parse_expression(self):
        """<expression> (Protected)

        Parses <expression> language structure.

            <expression> ::=
                <expression> '&' <arith_op> |
                <expression> '|' <arith_op> |
                [ 'not' ] <arith_op>
        """
        if self._accept('keyword', 'not'):
            pass

        self._parse_arith_op()

        while True:
            if self._accept('symbol', '&'):
                self._parse_arith_op()
            elif self._accept('symbol', '|'):
                self._parse_arith_op()
            else:
                break

        return

    def _parse_arith_op(self):
        """<arith_op> (Protected)

        Parses <arith_op> language structure.

            <arith_op> ::=
                <arith_op> '+' <relation> |
                <arith_op> '-' <relation> |
                <relation>
        """
        self._parse_relation()

        while True:
            if self._accept('symbol', '+'):
                self._parse_relation()
            elif self._accept('symbol', '-'):
                self._parse_relation()
            else:
                break

        return

    def _parse_relation(self):
        """<relation> (Protected)

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
        self._parse_term()

        while True:
            if self._accept('symbol', '<'):
                self._parse_term()
            elif self._accept('symbol', '>'):
                self._parse_term()
            elif self._accept('symbol', '<='):
                self._parse_term()
            elif self._accept('symbol', '>='):
                self._parse_term()
            elif self._accept('symbol', '=='):
                self._parse_term()
            elif self._accept('symbol', '!='):
                self._parse_term()
            else:
                break

        return

    def _parse_term(self):
        """<term> (Protected)

        Parses <term> language structure.

            <term> ::=
                <term> '*' <factor> |
                <term> '/' <factor> |
                <factor>
        """
        self._parse_factor()

        while True:
            if self._accept('symbol', '*'):
                self._parse_factor()
            elif self._accept('symbol', '/'):
                self._parse_factor()
            else:
                break

        return

    def _parse_factor(self):
        """<factor> (Protected)

        Parses <factor> language structure.

            <factor> ::=
                '(' <expression> ')' |
                [ '-' ] <name> |
                [ '-' ] <number> |
                <string> |
                'true' |
                'false'
        """
        if self._accept('symbol', '('):
            self._parse_expression()
            self._match('symbol', ')')
        elif self._accept('string'):
            pass
        elif self._accept('keyword', 'true'):
            pass
        elif self._accept('keyword', 'false'):
            pass
        elif self._accept('symbol', '-'):
            if self._first_name():
                self._parse_name()
            elif self._check('integer') or self._check('float'):
                self._parse_number()
            else:
                self._error('name or number')
        elif self._first_name():
            self._parse_name()
        elif self._check('integer') or self._check('float'):
            self._parse_number()
        else:
            self._error('factor')

        return

    def _first_name(self):
        """first(<name>) (Protected)

        Determines if current token matches the first terminals.

            first(<name>) ::=
                <identifier>

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self._check('identifier')

    def _parse_name(self):
        """<name> (Protected)

        Parses <name> language structure.

            <name> ::=
                <identifier> [ '[' <expression> ']' ]
        """
        self._match('identifier')

        if self._accept('symbol', '['):
            self._parse_expression()
            self._match('symbol', ']')

        return

    def _parse_number(self):
        """Parse Number (Protected)

        Parses the <number> language structure.

            <number> ::=
                [0-9][0-9_]*[.[0-9_]*]
        """
        if self._accept('integer'):
            pass
        elif self._accept('float'):
            pass
        else:
            self._error('number')

        return
