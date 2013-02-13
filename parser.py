#!/usr/bin/env python3

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
        token: The current token which is being parsed.
        debug: Boolean attribute denoting if successfully parsed tokens should
            be displayed as they are encountered and parsed.
    """
    def __init__(self, debug=False):
        super(Parser, self).__init__()

        # Public class attributes
        self.debug = debug

        # Define the current and future token holders
        self.current = None
        self.future = None

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
        self.advance_token()
        self.advance_token()

        # Begin parsing the <program> structure
        try:
            self.parse_program()
        except ParsingError as e:
            return False

        return True

    def error(self, expected):
        """Print Parser Error Message

        Prints a parser error message with details about the expected token
        and the current token being parsed.

        Arguments:
            expected: A string containing the expected token type/value.
        """
        token = self.current

        print('Error: "{0}", line {1}'.format(self._src_path, token.line))
        print('    Expected {0}, '.format(expected), end='')
        print('encountered \"{0}\" ({1})'.format(token.value, token.type))
        print('    {0}'.format(self._get_line(token.line)))

        # Raise an error and either bubble up to a resync point or fail out
        raise ParsingError(expected)

        return

    def advance_token(self):
        """Advance Tokens

        Populates the 'current' token with the 'future' token and populates
        the 'future' token with the next token in the source file.
        """
        self.current = self.future

        if self.future is None or self.future.type not in ['eof', 'error']:
            self.future = self.next_token()

        return

    def check(self, type, value=None, future=False):
        """Check Token

        Peeks at the token to see if the current token matches the given
        type and value. If it doesn't, don't make a big deal about it.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token.
            future: If True, the future (not current) token will be checked.

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        token = self.current

        if future:
            token = self.future

        return token.type == type and (token.value == value or value is None)

    def accept(self, type, value=None):
        """Accept Token

        Compares the token to an expected type and value. If it matches, then
        consume the token. If not, don't make a big deal about it.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token.

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        if self.check(type, value):
            if self.debug:
                print('>>> Consuming:', self.current)

            self.advance_token()
            return True

        return False

    def match(self, type, value=None):
        """Match Token

        Compares the token to an expected type and value. If it matches, then
        consume the token. If not, then throw an error and panic.

        Arguments:
            type: The expected type of the token.
            value: The expected value of the token.

        Returns:
            True if the token matches the expected value, False otherwise.
        """
        # Check the type, if we specified debug, print everything matchd
        if self.accept(type, value):
            return True

        # Something different than expected was encountered
        if type in ['identifier', 'integer', 'float', 'string']:
            self.error(type)
        else:
            self.error('"'+value+'"')

        return False

    def parse_program(self):
        """<program>

        Parses the <program> language structure.

            <program> ::=
                <program_header> <program_body>
        """
        self.parse_program_header()
        self.parse_program_body()

        return

    def parse_program_header(self):
        """<program_header>

        Parses the <program_header> language structure.

            <program_header> ::=
                'program' <identifier> 'is'
        """
        self.match('keyword', 'program')
        self.match('identifier')
        self.match('keyword', 'is')

        return

    def parse_program_body(self):
        """<program_body>

        Parses the <program_body> language structure.

            <program_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'program'
        """
        while not self.accept('keyword', 'begin'):
            self.parse_declaration()
            self.match('symbol', ';')

        while not self.accept('keyword', 'end'):
            self.parse_statement()
            self.match('symbol', ';')

        self.match('keyword', 'program')

        return

    def parse_declaration(self):
        """<declaration>

        Parses the <declaration> language structure.

            <declaration> ::=
                [ 'global' ] <procedure_declaration>
                [ 'global' ] <variable_declaration>
        """
        if self.accept('keyword', 'global'):
            pass

        if self.first_procedure_declaration():
            self.parse_procedure_declaration()
        elif self.first_variable_declaration():
            self.parse_variable_declaration()
        else:
            self.error('declaration')

        return

    def first_variable_declaration(self):
        """first(<variable_declaration>)

        Determines if current token matches the first terminals.

            first(<variable_declaration>) ::=
                integer | float | bool | string

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return (self.check('keyword', 'integer') or
                self.check('keyword', 'float') or
                self.check('keyword', 'bool') or
                self.check('keyword', 'string'))

    def parse_variable_declaration(self):
        """<variable_declaration>

        Parses the <variable_declaration> language structure.

            <variable_declaration> ::=
                <type_mark> <identifier> [ '[' <array_size> ']' ]
        """
        if self.accept('keyword', 'integer'):
            pass
        elif self.accept('keyword', 'float'):
            pass
        elif self.accept('keyword', 'bool'):
            pass
        elif self.accept('keyword', 'string'):
            pass
        else:
            self.error('variable declaration')
            return

        self.match('identifier')

        if self.accept('symbol', '['):
            self.parse_number()
            self.match('symbol', ']')

        return

    def first_procedure_declaration(self):
        """first(<procedure_declarations>)

        Determines if current token matches the first terminals.

            first(<procedure_declaration>) ::=
                'procedure'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.check('keyword', 'procedure')

    def parse_procedure_declaration(self):
        """<procedure_declaration>

        Parses the <procedure_declaration> language structure.

            <procedure_declaration> ::=
                <procedure_header> <procedure_body>
        """
        self.parse_procedure_header()
        self.parse_procedure_body()

        return

    def parse_procedure_header(self):
        """<procedure_header>

        Parses the <procedure_header> language structure.

            <procedure_header> ::=
                'procedure' <identifier> '(' [ <parameter_list> ] ')'
        """
        self.match('keyword', 'procedure')
        self.match('identifier')
        self.match('symbol', '(')

        if not self.check('symbol', ')'):
            self.parse_parameter_list()

        self.match('symbol', ')')

        return

    def parse_procedure_body(self):
        """<procedure_body>

        Parses the <procedure_body> language structure.

            <procedure_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'procedure'
        """
        while not self.accept('keyword', 'begin'):
            self.parse_declaration()
            self.match('symbol', ';')

        while not self.accept('keyword', 'end'):
            self.parse_statement()
            self.match('symbol', ';')

        self.match('keyword', 'procedure')

        return

    def parse_parameter_list(self):
        """<parameter_list>

        Parse the <parameter_list> language structure.

            <parameter_list> ::=
                <parameter> ',' <parameter_list> |
                <parameter>
        """
        self.parse_parameter()

        if self.accept('symbol', ','):
            self.parse_parameter_list()

        return

    def parse_parameter(self):
        """<parameter>

        Parse the <parameter> language structure.

            <parameter> ::=
                <variable_declaration> ( 'in' | 'out' )
        """
        self.parse_variable_declaration()

        if self.accept('keyword', 'in'):
            pass
        elif self.accept('keyword', 'out'):
            pass
        else:
            self.error('\"in\" or \"out\"')

        return

    def parse_statement(self):
        """<statement>

        Parse the <statement> language structure.

            <statement> ::=
                <assignment_statement> |
                <if_statement> |
                <loop_statement> |
                <return_statement> |
                <procedure_call>
        """
        if self.accept('keyword', 'return'):
            pass
        elif self.first_if_statement():
            self.parse_if_statement()
        elif self.first_loop_statement():
            self.parse_loop_statement()
        elif self.first_procedure_call():
            self.parse_procedure_call()
        elif self.first_assignment_statement():
            self.parse_assignment_statement()
        else:
            self.error('statement')

        return

    def first_assignment_statement(self):
        """first(<assignment_statement>)

        Determines if current token matches the first terminals.

            first(<assignment_statement>) ::=
                <identifier>

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.check('identifier')

    def parse_assignment_statement(self):
        """<assignment_statement>

        Parses the <assignment_statement> language structure.

            <assignment_statement> ::=
                <destination> ':=' <expression>
        """
        self.parse_destination()
        self.match('symbol', ':=')
        self.parse_expression()

        return

    def first_if_statement(self):
        """first(<if_statement>)

        Determines if current token matches the first terminals.

            first(<if_statement>) ::=
                'if'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.check('keyword', 'if')

    def parse_if_statement(self):
        """<if_statement>

        Parses the <if_statement> language structure.

            <if_statement> ::=
                'if' '(' <expression> ')' 'then' ( <statement> ';' )+
                [ 'else' ( <statement> ';' )+ ]
                'end' 'if'
        """
        self.match('keyword', 'if')
        self.match('symbol', '(')

        self.parse_expression()

        self.match('symbol', ')')
        self.match('keyword', 'then')

        while True:
            self.parse_statement()
            self.match('symbol', ';')

            if self.check('keyword', 'else') or self.check('keyword', 'end'):
                break

        if self.accept('keyword', 'else'):
            while True:
                self.parse_statement()
                self.match('symbol', ';')

                if self.check('keyword', 'end'):
                    break

        self.match('keyword', 'end')
        self.match('keyword', 'if')

        return

    def first_loop_statement(self):
        """first(<loop_statement>)

        Determines if current token matches the first terminals.

            first(<loop_statement>) ::=
                'for'

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.check('keyword', 'for')

    def parse_loop_statement(self):
        """<loop_statement>

        Parses the <loop_statement> language structure.

            <loop_statement> ::=
                'for' '(' <assignment_statement> ';' <expression> ')'
                    ( <statement> ';' )*
                'end' 'for'
        """
        self.match('keyword', 'for')
        self.match('symbol', '(')
        self.parse_assignment_statement()
        self.match('symbol', ';')
        self.parse_expression()
        self.match('symbol', ')')

        while not self.accept('keyword', 'end'):
            self.parse_statement()
            self.match('symbol', ';')

        self.match('keyword', 'for')

        return

    def first_procedure_call(self):
        """first(<procedure_call>)

        Determines if current token matches the first terminals. The second
        terminal is checked using the future token in this case to distinguish
        the first(<procedure_call>) from first(<assignment_statement>).

            first(<procedure_call>) ::=
                '('

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.check('symbol', '(', future=True)

    def parse_procedure_call(self):
        """<procedure_call>

        Parses the <procedure_call> language structure.

            <procedure_call> ::=
                <identifier> '(' [ <argument_list> ] ')'
        """
        self.match('identifier')
        self.match('symbol', '(')

        if not self.check('symbol', ')'):
            self.parse_argument_list()

        self.match('symbol', ')')

        return

    def parse_argument_list(self):
        """<argument_list>

        Parses <argument_list> language structure.

            <argument_list> ::=
                <expression> ',' <argument_list> |
                <expression>
        """
        self.parse_expression()

        if self.accept('symbol', ','):
            self.parse_argument_list()

        return

    def parse_destination(self):
        """<destination>

        Parses the <destination> language structure.

            <destination> ::=
                <identifier> [ '[' <expression> ']' ]
        """
        self.match('identifier')

        if self.accept('symbol', '['):
            self.parse_expression()
            self.accept('symbol', ']')

        return

    def parse_expression(self):
        """<expression>

        Parses <expression> language structure.

            <expression> ::=
                <expression> '&' <arith_op> |
                <expression> '|' <arith_op> |
                [ 'not' ] <arith_op>
        """
        if self.accept('keyword', 'not'):
            pass

        self.parse_arith_op()

        while True:
            if self.accept('symbol', '&'):
                self.parse_arith_op()
            elif self.accept('symbol', '|'):
                self.parse_arith_op()
            else:
                break

        return

    def parse_arith_op(self):
        """<arith_op>

        Parses <arith_op> language structure.

            <arith_op> ::=
                <arith_op> '+' <relation> |
                <arith_op> '-' <relation> |
                <relation>
        """
        self.parse_relation()

        while True:
            if self.accept('symbol', '+'):
                self.parse_relation()
            elif self.accept('symbol', '-'):
                self.parse_relation()
            else:
                break

        return

    def parse_relation(self):
        """<relation>

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
        self.parse_term()

        while True:
            if self.accept('symbol', '<'):
                self.parse_term()
            elif self.accept('symbol', '>'):
                self.parse_term()
            elif self.accept('symbol', '<='):
                self.parse_term()
            elif self.accept('symbol', '>='):
                self.parse_term()
            elif self.accept('symbol', '=='):
                self.parse_term()
            elif self.accept('symbol', '!='):
                self.parse_term()
            else:
                break

        return

    def parse_term(self):
        """<term>

        Parses <term> language structure.

            <term> ::=
                <term> '*' <factor> |
                <term> '/' <factor> |
                <factor>
        """
        self.parse_factor()

        while True:
            if self.accept('symbol', '*'):
                self.parse_factor()
            elif self.accept('symbol', '/'):
                self.parse_factor()
            else:
                break

        return

    def parse_factor(self):
        """<factor>

        Parses <factor> language structure.

            <factor> ::=
                '(' <expression> ')' |
                [ '-' ] <name> |
                [ '-' ] <number> |
                <string> |
                'true' |
                'false'
        """
        if self.accept('symbol', '('):
            self.parse_expression()
            self.match('symbol', ')')
        elif self.accept('string'):
            pass
        elif self.accept('keyword', 'true'):
            pass
        elif self.accept('keyword', 'false'):
            pass
        elif self.accept('symbol', '-'):
            if self.first_name():
                self.parse_name()
            elif self.check('integer') or self.check('float'):
                self.parse_number()
            else:
                self.error('name or number')
        elif self.first_name():
            self.parse_name()
        elif self.check('integer') or self.check('float'):
            self.parse_number()
        else:
            self.error('factor')

        return

    def first_name(self):
        """first(<name>)

        Determines if current token matches the first terminals.

            first(<name>) ::=
                <identifier>

        Returns:
            True if current token matches a first terminal, False otherwise.
        """
        return self.check('identifier')

    def parse_name(self):
        """<name>

        Parses <name> language structure.

            <name> ::=
                <identifier> [ '[' <expression> ']' ]
        """
        self.match('identifier')

        if self.accept('symbol', '['):
            self.parse_expression()
            self.match('symbol', ']')

        return

    def parse_number(self):
        """Parse Number

        Parses the <number> language structure.

            <number> ::=
                [0-9][0-9_]*[.[0-9_]*]
        """
        if self.accept('integer'):
            pass
        elif self.accept('float'):
            pass
        else:
            self.error('number')

        return
