#!/usr/bin/env python3

"""Parser module

Inherits the Scanner module and parses the attached file's tokens as they are
encountered with the target grammar. Code is then generated and written to the
given destination file.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    Parser: An implementation of a parser for the source language.
"""

from lib.errors import *
from lib.datatypes import Identifier, Parameter, IdentifierTable

from lib.scanner import Scanner
from lib.codegenerator import CodeGenerator


class Parser(Scanner, CodeGenerator):
    """Parser class

    Parses the given source file using the defined language structure.

    Inherits:
        Scanner: The lexer component of the compiler.
        CodeGenerator: The class responsible for output file abstraction.

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

        # Define the identifier table to hold all var/program/procedure names
        self._ids = IdentifierTable()

        self._has_errors = False

        return

    def parse(self, src_path, dest_path):
        """Begin Parsing

        Begins the parse of the inputted source file.

        Arguments:
            src_path: The input source file to parse.
            dest_path: The output target file to write.

        Returns:
            True on success, False otherwise.
        """
        # Attach the source file for reading
        if not self.attach_source(src_path):
            return False

        # Attach the destination file for writing
        if not self.attach_destination(dest_path):
            return False

        # Generate the compiled code header to handle runtime overhead
        self.generate_header()

        # Advance the tokens twice to populate both current and future tokens
        self._advance_token()
        self._advance_token()

        # Begin parsing the root <program> language structure
        try:
            self._parse_program()
        except ParserSyntaxError:
            return False

        # Make sure there's no junk after the end of program
        if not self._check('eof'):
            self._warning('eof')

        if not self._has_errors:
            self.commit()
        else:
            self.rollback()

        return True

    def _warning(self, msg, line, prefix='Warning'):
        """Print Parser Warning Message (Protected)

        Prints a parser warning message with details about the expected token
        and the current token being parsed.

        Arguments:
            msg: The warning message to display.
            line: The line where the warning has occurred.
            prefix: A string value to be printed at the start of the warning.
                Overwritten for error messages. (Default: 'Warning')
        """
        print('{0}: "{1}", line {2}'.format(prefix, self._src_path, line))
        print('    {0}'.format(msg))
        print('    {0}'.format(self._get_line(line)))

        return

    def _syntax_error(self, expected):
        """Print Syntax Error Message (Protected)

        Prints a syntax error message with details about the expected token
        and the current token being parsed. After error printing, an exception
        is raised to be caught and resolved by parent nodes.

        Arguments:
            expected: A string containing the expected token type/value.

        Raises:
            ParserSyntaxError: If this method is being called, an error has been
                encountered during parsing.
        """
        token = self._current

        # Print the error message
        msg = 'Expected {0}, encountered "{1}" ({2})'.format(
                expected, token.value, token.type)
        self._warning(msg, token.line, prefix='Error')

        self._has_errors = True
        raise ParserSyntaxError()

    def _name_error(self, msg, name, line):
        """Print Name Error Message (Protected)

        Prints a name error message with details about the encountered
        identifier which caused the error.

        Arguments:
            msg: The reason for the error.
            name: The name of the identifier where the name error occured.
            line: The line where the name error occured.
        """
        msg = '{0}: {1}'.format(name, msg)
        self._warning(msg, line, prefix='Error')

        self._has_errors = True
        return

    def _type_error(self, expected, encountered, line):
        """Print Type Error Message (Protected)

        Prints a type error message with details about the expected type an
        the type that was encountered.

        Arguments:
            expected: A string containing the expected token type.
            encountered: A string containing the type encountered.
            line: The line on which the type error occurred.
        """
        msg = 'Expected {0} type, encountered {1}'.format(expected, encountered)
        self._warning(msg, line, prefix='Error')

        self._has_errors = True
        return

    def _runtime_error(self, msg, line):
        """Print Runtime Error Message (Protected)

        Prints a runtime error message with details about the runtime error.

        Arguments:
            msg: The reason for the error.
            line: The line where the runtime error occured.
        """
        self._warning(msg, line, prefix='Error')

        self._has_errors = True
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
            self._syntax_error('"'+value+'" ('+type+')')
        else:
            self._syntax_error(type)

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

        # Add the new identifier to the global table
        id = Identifier(id_name, 'program', None, None)
        self._ids.add(id, is_global=True)

        self._match('keyword', 'is')

        # Push the scope to the program body level
        self._ids.push_scope()

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
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'program')

        # Pop out of the program body scope
        self._ids.pop_scope()

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
            self._parse_procedure_declaration(is_global=is_global)
        elif self._first_variable_declaration():
            self._parse_variable_declaration(is_global=is_global)
        else:
            self._syntax_error('procedure or variable declaration')

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

    def _parse_variable_declaration(self, is_global=False, id_table_add=True):
        """<variable_declaration> (Protected)

        Parses the <variable_declaration> language structure.

            <variable_declaration> ::=
                <type_mark> <identifier> [ '[' <array_size> ']' ]

        Arguments:
            is_global: Denotes if the variable is to be globally scoped.
                (Default: False)
            id_table_add: Denotes if the variable is to be added to the
                identifier table.

        Returns:
            The Identifier class object of the variable encountered.
        """
        id_type = self._parse_type_mark()

        # Start collecting info about the identifier
        id_name = self._current.value
        id_line = self._current.line
        id_size = None

        # Formally match the token to an identifier type
        self._match('identifier')

        if self._accept('symbol', '['):
            id_size = self._current.value
            index_line = self._current.line
            index_type = self._parse_number()

            # Check the type to make sure this is an integer so that we can
            # allocate memory appropriately
            if  index_type != 'integer':
                self._type_error('integer', index_type, index_line)
                raise ParserTypeError()

            self._match('symbol', ']')

        # The declaration was valid, add the identifier to the table
        id = Identifier(name=id_name, type=id_type, size=id_size, params=None)

        if id_table_add:
            try:
                self._ids.add(id, is_global=is_global)
            except ParserNameError:
                self._name_error('name already declared at this scope', id_name,
                        id_line)

        return id

    def _parse_type_mark(self):
        """<type_mark> (Protected)

        Parses <type_mark> language structure.

            <type_mark> ::=
                'integer' |
                'float' |
                'bool' |
                'string'

        Returns:
            Type (as string) of the variable being declared.
        """
        type = None

        if self._accept('keyword', 'integer'):
            type = 'integer'
        elif self._accept('keyword', 'float'):
            type = 'float'
        elif self._accept('keyword', 'bool'):
            type = 'bool'
        elif self._accept('keyword', 'string'):
            type = 'string'
        else:
            self._syntax_error('variable type')

        return type

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
        self._parse_procedure_header(is_global=is_global)
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
        self._match('keyword', 'procedure')

        id_name = self._current.value
        id_line = self._current.line

        self._match('identifier')
        self._match('symbol', '(')

        params = []

        if not self._check('symbol', ')'):
            params = self._parse_parameter_list()

        self._match('symbol', ')')

        id = Identifier(id_name, 'procedure', None, params)

        try:
            # Add the procedure identifier to the parent and its own table
            self._ids.add(id, is_global=is_global)
            self._ids.push_scope()
            self._ids.add(id)
        except ParserNameError as e:
            self._name_error('name already declared at this scope', id_name,
                    id_line)

        # Attempt to add each encountered param at the procedure scope
        for param in params:
            try:
                self._ids.add(param.id, is_global=False)
            except ParserNameError:
                self._name_error('name already declared at global scope',
                        param.id.name, id_line)

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
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'procedure')

        self._ids.pop_scope()

        return

    def _parse_parameter_list(self, params=[]):
        """<parameter_list> (Protected)

        Parse the <parameter_list> language structure.

            <parameter_list> ::=
                <parameter> ',' <parameter_list> |
                <parameter>

        Arguments:
            params: A list of Parameter namedtuples associated with the
                procedure. (Default: None)

        Returns:
            An completed list of all Parameter namedtuples associated
            with the procedure.
        """
        param = self._parse_parameter()
        params.append(param)

        if self._accept('symbol', ','):
            params = self._parse_parameter_list(params)

        return params

    def _parse_parameter(self):
        """<parameter> (Protected)

        Parse the <parameter> language structure.

            <parameter> ::=
                <variable_declaration> ( 'in' | 'out' )
        """
        id = self._parse_variable_declaration(id_table_add=False)

        direction = None

        if self._accept('keyword', 'in'):
            direction = 'in'
        elif self._accept('keyword', 'out'):
            direction = 'out'
        else:
            self._syntax_error('"in" or "out"')

        return Parameter(id, direction)

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
            self._syntax_error('statement')

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
        line = self._current.line

        dest_type = self._parse_destination()
        self._match('symbol', ':=')
        expr_type = self._parse_expression()

        if dest_type != expr_type:
            self._type_error(dest_type, expr_type, line)

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
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

            if self._check('keyword', 'else') or self._check('keyword', 'end'):
                break

        if self._accept('keyword', 'else'):
            while True:
                try:
                    self._parse_statement()
                except ParserError:
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
        except ParserError:
            self._resync_at_token('symbol', ';')

        self._match('symbol', ';')
        self._parse_expression()
        self._match('symbol', ')')

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except ParserError:
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
        # Match an identifier, check to make sure the identifier is procedure
        id = None
        id_name = self._current.value
        id_line = self._current.line
        id_type = None

        self._match('identifier')

        try:
            id = self._ids.find(id_name)
        except ParserNameError as e:
            self._name_error('procedure has not beed declared', id_name,
                    id_line)
            raise e

        if id.type != 'procedure':
            self._type_error('procedure', id.type, id_line)
            raise ParserTypeError()

        self._match('symbol', '(')

        if not self._check('symbol', ')'):
            num_args = self._parse_argument_list(id.params)

            # Make sure that too few arguments are not used
            if num_args < len(id.params):
                self._runtime_error(('procedure call accepts %d argument(s),' +
                        ' %d given') % (len(id.params), num_args), id_line)
                raise ParserRuntimeError()

        self._match('symbol', ')')

        return

    def _parse_argument_list(self, params, index=0):
        """<argument_list> (Protected)

        Parses <argument_list> language structure.

            <argument_list> ::=
                <expression> ',' <argument_list> |
                <expression>

        Arguments:
            params: A list of Parameter namedtuple objects allowed in the
                procedure call
            index: The index in params with which to match the found param.
                (Default: 0)

        Returns:
            The number of arguments encountered.
        """
        line = self._current.line

        # Make sure that too many arguments are not used
        if index > len(params) - 1:
            self._runtime_error('procedure call accepts only %d argument(s)' %
                    len(params), line)
            raise ParserRuntimeError()

        param = params[index]

        arg_type = self._parse_expression()

        if arg_type != param.id.type:
            self._type_error(param.id.type, arg_type, line)

        index += 1

        if self._accept('symbol', ','):
            index = self._parse_argument_list(params, index)

        return index

    def _parse_destination(self):
        """<destination> (Protected)

        Parses the <destination> language structure.

            <destination> ::=
                <identifier> [ '[' <expression> ']' ]

        Returns:
            Type of the destination identifier as a string.
        """
        id = None

        id_name = self._current.value
        id_line = self._current.line
        id_type = None

        self._match('identifier')

        # Make sure that identifier is valid for the scope
        try:
            id = self._ids.find(id_name)
        except ParserNameError as e:
            self._name_error('not declared in this scope', id_name, id_line)
            raise e

        # Check type to make sure it's a variable
        if not id.type in ['integer', 'float', 'bool', 'string']:
            self._type_error('variable', id.type, id_line)
            raise ParserTypeError()

        id_type = id.type

        if self._accept('symbol', '['):
            expr_line = self._current.line
            expr_type = self._parse_expression()

            if expr_type != 'integer':
                self._type_error('integer', expr_type, expr_line)

            self._accept('symbol', ']')

        return id_type

    def _parse_expression(self):
        """<expression> (Protected)

        Parses <expression> language structure.

            <expression> ::=
                <expression> '&' <arith_op> |
                <expression> '|' <arith_op> |
                [ 'not' ] <arith_op>

        Returns:
            The type value of the expression.
        """
        expect_int_or_bool = False

        if self._accept('keyword', 'not'):
            expect_int_or_bool = True

        line = self._current.line
        type = self._parse_arith_op()

        if expect_int_or_bool and type not in ['integer', 'bool']:
            self._type_error('integer or bool', type, line)
            raise ParserTypeError()

        while True:
            if self._accept('symbol', '&'):
                pass
            elif self._accept('symbol', '|'):
                pass
            else:
                break

            if type not in ['integer', 'bool']:
                self._type_error('integer or bool', type, line)
                raise ParserTypeError()

            next_type = self._parse_arith_op()

            if next_type not in ['integer', 'bool']:
                self._type_error('integer or bool', next_type, line)
                raise ParserTypeError()

        return type

    def _parse_arith_op(self):
        """<arith_op> (Protected)

        Parses <arith_op> language structure.

            <arith_op> ::=
                <arith_op> '+' <relation> |
                <arith_op> '-' <relation> |
                <relation>

        Returns:
            The type value of the expression.
        """
        line = self._current.line
        type = self._parse_relation()

        while True:
            if self._accept('symbol', '+'):
                pass
            elif self._accept('symbol', '-'):
                pass
            else:
                break

            if type not in ['integer', 'float']:
                self._type_error('integer or float', type, line)
                raise ParserTypeError()

            next_type = self._parse_relation()

            if next_type not in ['integer', 'float']:
                self._type_error('integer or float', next_type, line)
                raise ParserTypeError()

        return type

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

        Returns:
            The type value of the expression.
        """
        line = self._current.line
        type = self._parse_term()

        # Check for relational operators. Note that relational operators
        # are only valid for integers or booleans
        while True:
            if self._accept('symbol', '<'):
                pass
            elif self._accept('symbol', '>'):
                pass
            elif self._accept('symbol', '<='):
                pass
            elif self._accept('symbol', '>='):
                pass
            elif self._accept('symbol', '=='):
                pass
            elif self._accept('symbol', '!='):
                pass
            else:
                break

            if type not in ['integer', 'bool']:
                self._type_error('integer or bool', type, line)
                raise ParserTypeError()

            next_type = self._parse_term()

            if next_type not in ['integer', 'bool']:
                self._type_error('integer or bool', next_type, line)
                raise ParserTypeError()

        return type

    def _parse_term(self):
        """<term> (Protected)

        Parses <term> language structure.

            <term> ::=
                <term> '*' <factor> |
                <term> '/' <factor> |
                <factor>

        Returns:
            The type value of the expression.
        """
        line = self._current.line
        type = self._parse_factor()

        # Check for multiplication or division operators. Note that these
        # operators are only valid for integer or float values
        while True:
            if self._accept('symbol', '*'):
                pass
            elif self._accept('symbol', '/'):
                pass
            else:
                break

            if type not in ['integer', 'float']:
                self._type_error('integer or float', type, line)
                raise ParserTypeError()

            next_type = self._parse_factor()

            if next_type not in ['integer', 'float']:
                self._type_error('integer or float', next_type, line)
                raise ParserTypeError()

        return type

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

        Returns:
            The type value of the expression.
        """
        type = None

        if self._accept('symbol', '('):
            type = self._parse_expression()
            self._match('symbol', ')')
        elif self._accept('string'):
            type = 'string'
        elif self._accept('keyword', 'true'):
            type = 'bool'
        elif self._accept('keyword', 'false'):
            type = 'bool'
        elif self._accept('symbol', '-'):
            if self._first_name():
                type = self._parse_name()
            elif self._check('integer') or self._check('float'):
                type = self._parse_number()
            else:
                self._syntax_error('variable name, integer, or float')
        elif self._first_name():
            type = self._parse_name()
        elif self._check('integer') or self._check('float'):
            type = self._parse_number()
        else:
            self._syntax_error('factor')

        return type

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
        id_name = self._current.value
        id_line = self._current.line
        id_type = None

        self._match('identifier')

        # Make sure that identifier is valid for the scope
        try:
            id = self._ids.find(id_name)
            id_type = id.type
        except ParserNameError as e:
            self._name_error('not declared in this scope', id_name, id_line)
            raise e

        # Check type to make sure it's a variable
        if not id_type in ['integer', 'float', 'bool', 'string']:
            self._type_error('variable', id_type, id_line)
            raise ParserTypeError()

        if self._accept('symbol', '['):
            index_type = self._parse_expression()

            if not index_type == 'integer':
                self._type_error('integer', index_type, id_line)
                raise ParserTypeError()

            self._match('symbol', ']')

        return id_type

    def _parse_number(self):
        """Parse Number (Protected)

        Parses the <number> language structure.

            <number> ::=
                [0-9][0-9_]*[.[0-9_]*]

        Returns:
            Type (as a string) of the parsed number.
        """
        type = None

        if self._accept('integer'):
            type = 'integer'
        elif self._accept('float'):
            type = 'float'
        else:
            self._syntax_error('number')

        return type
