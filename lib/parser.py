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

        # Define the previous, current, and future token holder
        self._previous = None
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

        # Add all runtime functions
        self._add_runtime()

        # Begin parsing the root <program> language structure
        try:
            self._parse_program()
        except ParserSyntaxError:
            return False

        # Generate the compiled code footer
        self.generate_footer()

        # Make sure there's no junk after the end of program
        if not self._check('eof'):
            self._warning('eof')

        if not self._has_errors:
            self.commit()
        else:
            self.rollback()

        return True

    def _add_runtime(self):
        """Add Runtime Functions

        Adds each runtime function to the list of global functions.
        """
        # The runtime_functions list is defined in the CodeGenerator class
        for func_name in iter(self.runtime_functions):
            # Get all parameters for these functions
            param_ids = []
            param_list = self.runtime_functions[func_name]
            for index, param in enumerate(param_list):
                # Build up each param, add it to the list
                id_obj = Identifier(name=param[0], type=param[1], size=None,
                        params=None, mm_ptr=(index+1))
                p_obj = Parameter(id=id_obj, direction=param[2])
                param_ids.append(p_obj)

            # Build the function's identifier
            func_id = Identifier(name=func_name, type='procedure', size=None, 
                    params=param_ids, mm_ptr=1)

            self._ids.add(func_id, is_global=True)

        return

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
        self._previous = self._current
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
            #if self.debug:
            #    print('>>> Consuming:', self._current)

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
            The matched Token class object if successful.
        """
        # Check the type, if we specified debug, print everything matchd
        if self._accept(type, value):
            return self._previous

        # Something different than expected was encountered
        if value is not None:
            self._syntax_error('"'+value+'" ('+type+')')
        else:
            self._syntax_error(type)

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
        id = self._parse_program_header()
        self._parse_program_body(id)

        return

    def _parse_program_header(self):
        """<program_header> (Protected)

        Parses the <program_header> language structure.

            <program_header> ::=
                'program' <identifier> 'is'

        Returns:
            The id object with information about the procedure identifier.
        """
        self._match('keyword', 'program')

        id_name = self._current.value
        self._match('identifier')

        # Generate procedure label. This will be stored with the identifier
        # in place of the mm_ptr attribute since it will not be used
        label_id = self.get_label_id()

        # Add the new identifier to the global table
        id = Identifier(id_name, 'program', None, None, label_id)
        self._ids.add(id, is_global=True)

        self._match('keyword', 'is')

        # Push the return addr onto the stack
        self.comment('Setting program return address', self.debug)
        self.generate('MM[R[FP]] = (int)&&%s_%d_end;' % (id.name, id.mm_ptr))

        # Make the jump to the entry point
        self.generate('goto %s_%d_begin;' % (id.name, id.mm_ptr))

        # Make the main program return
        self.generate('')
        self.comment('Creating the program exit point', self.debug)
        self.generate('%s_%d_end:' % (id.name, id.mm_ptr))
        self.tab_push()
        self.generate('return 0;');
        self.tab_pop()
        self.generate('')
                
        # Push the scope to the program body level
        self._ids.push_scope(id.name)

        # Add the program to the base scope so it can be resolved as owner
        self._ids.add(id)

        return id

    def _parse_program_body(self, id):
        """<program_body> (Protected)

        Parses the <program_body> language structure.

            <program_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'program'

        Arguments:
            id: The identifier object for the program.
        """
        local_var_size = 0

        while not self._accept('keyword', 'begin'):
            try:
                size = self._parse_declaration()

                if size is not None:
                    local_var_size += int(size)
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        # Label the entry point for the program
        self.generate('%s_%d_begin:' % (id.name, id.mm_ptr))
        self.tab_push()

        if local_var_size != 0:
            self.comment('Allocating space for local variables', self.debug)
            self.generate('R[SP] = R[SP] - %d;' % local_var_size)

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'program')

        # Pop out of the program body scope
        self._ids.pop_scope()
        self.tab_pop()

        return

    def _parse_declaration(self):
        """<declaration> (Protected)

        Parses the <declaration> language structure.

            <declaration> ::=
                [ 'global' ] <procedure_declaration>
                [ 'global' ] <variable_declaration>

        Returns:
            The size of any variable declared. None if procedure.
        """
        is_global = False

        id = None
        size = None

        if self._accept('keyword', 'global'):
            is_global = True

        if self._first_procedure_declaration():
            self._parse_procedure_declaration(is_global=is_global)
        elif self._first_variable_declaration():
            id = self._parse_variable_declaration(is_global=is_global)
        else:
            self._syntax_error('procedure or variable declaration')

        if id is not None:
            size = id.size if id.size is not None else 1

        return size

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

    def _parse_variable_declaration(self, is_global=False, is_param=False):
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

        # Stores the array size of the variable
        var_size = None

        # Formally match the token to an identifier type
        var_token = self._match('identifier')

        if self._accept('symbol', '['):
            index_type = self._parse_number()

            var_size = self._previous.value
            index_line = self._previous.line

            # Check the type to make sure this is an integer so that we can
            # allocate memory appropriately
            if  index_type != 'integer':
                self._type_error('integer', index_type, index_line)
                raise ParserTypeError()

            self._match('symbol', ']')

        # Get the memory space pointer for this variable.
        mm_ptr = self.get_mm(var_size, is_global=is_global, is_param=is_param)

        # The declaration was valid, add the identifier to the table
        id = Identifier(var_token.value, id_type, var_size, None, mm_ptr)

        if not is_param:
            try:
                self._ids.add(id, is_global=is_global)
            except ParserNameError:
                self._name_error('name already declared at this scope',
                        var_token.value, var_token.line)

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
        id = self._parse_procedure_header(is_global=is_global)
        self._parse_procedure_body(id)

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

        # Generate procedure label. This will be stored with the identifier
        # in place of the mm_ptr attribute since it will not be used
        label_id = self.get_label_id()

        id = Identifier(id_name, 'procedure', None, params, label_id)

        try:
            # Add the procedure identifier to the parent and its own table
            self._ids.add(id, is_global=is_global)
            self._ids.push_scope(id.name)
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

        # Define the entry point for the function w/ unique identifier
        self.generate('%s_%d:' % (id.name, id.mm_ptr))
        self.tab_push()

        # Define the begining of the function body
        self.generate('goto %s_%d_begin;' % (id.name, id.mm_ptr))
        self.generate('')

        return id

    def _parse_procedure_body(self, id):
        """<procedure_body> (Protected)

        Parses the <procedure_body> language structure.

            <procedure_body> ::=
                    ( <declaration> ';' )*
                'begin'
                    ( <statement> ';' )*
                'end' 'procedure'

        Arguments:
            id: The identifier object for the procedure.
        """
        local_var_size = 0

        # Reset the local pointer for the local variables.
        self.reset_local_ptr()
        self.reset_param_ptr()

        # Accept any declarations
        while not self._accept('keyword', 'begin'):
            try:
                size = self._parse_declaration()

                # If this was a local var, allocate space for it
                if size is not None:
                    local_var_size += size
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        # Define the function begin point
        self.generate('%s_%d_begin:' % (id.name, id.mm_ptr))
        self.tab_push()

        if local_var_size != 0:
            self.comment('Allocating space for local variables', self.debug)
            self.generate('R[SP] = R[SP] - %d;' % local_var_size)

        # Accept any statements
        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'procedure')

        # Smash the local stack
        self.comment('Movin SP to FP (retun address)', self.debug)
        self.generate('R[SP] = R[FP];')

        # Goto the return label to exit the procedure
        self.comment('Return to calling functon', self.debug)
        self.generate('goto *(void*)MM[R[FP]];')
        self.generate('')

        self.tab_pop()
        self._ids.pop_scope()
        self.tab_pop()

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
        # Get one parameter
        param = self._parse_parameter()
        params.append(param)

        # Get all following parameters
        if self._accept('symbol', ','):
            params = self._parse_parameter_list(params)

        # All parameters found will be returned in the list
        return params

    def _parse_parameter(self):
        """<parameter> (Protected)

        Parse the <parameter> language structure.

            <parameter> ::=
                <variable_declaration> ( 'in' | 'out' )
        """
        # Return the id object, but don't add it to the identifier table
        # yet or get a memory location for it. This will be done when the
        # procedure is called
        id = self._parse_variable_declaration(is_param=True)

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
            # Goto the return label to exit the procedure/program
            self.generate('goto *(void*)MM[R[FP]];')
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

        id_name = self._current.value
        dest_type = self._parse_destination()

        # Grab the last register used in case this variable is an array
        index_reg = self.get_reg(inc=False)

        # Check to make sure this is a valid identifier
        id_obj = self._ids.find(id_name)

        self._match('symbol', ':=')

        expr_type = self._parse_expression()

        # Get the register used for the expression
        expr_reg = self.get_reg(inc=False)

        if dest_type != expr_type:
            self._type_error(dest_type, expr_type, line)

        # Get a new register to calculate the main memory addr of this id
        id_reg = self.get_reg()

        # If identifier is param, mm_ptr will be the parameter offset
        # If identifier is local, mm_ptr will be the local offset
        # If identifier is global, mm_ptr is the direct memory space
        self.generate('R[%d] = %d;' % (id_reg, id_obj.mm_ptr))

        if id_obj.size is not None:
            self.generate('R[%d] = R[%d] + R[%d];' % (id_reg, id_reg, index_reg))

        if self._ids.is_param(id_obj.name):
            # Make sure that this is an 'in' parameter only
            direction = self._ids.get_param_direction(id_obj.name)
            if direction != 'out':
                self._type_error('\'out\' param',
                        '\'%s\' param' % direction, line)
                raise ParserTypeError()

            # Calculate the parameter location
            self.comment('Param referenced', self.debug)
            self.generate('R[%d] = R[FP] + 1 + R[%d];' % (id_reg, id_reg))
        elif not self._ids.is_global(id_obj.name):
            self.comment('Local var referenced', self.debug)
            self.generate('R[%d] = R[FP] - R[%d];' % (id_reg, id_reg))
        else:
            self.comment('Global var referenced', self.debug)

        self.generate('MM[R[%d]] = R[%d];' % (id_reg, expr_reg))

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

        label_id = self.get_label_id()
        expr_reg = self.get_reg(inc=False)

        self.generate('if (!R[%d]) goto else_%d;' % (expr_reg, label_id))
        self.tab_push()

        while True:
            try:
                self._parse_statement()
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

            if self._check('keyword', 'else') or self._check('keyword', 'end'):
                break

        self.generate('goto endif_%d;' % label_id)

        self.tab_pop()
        self.generate('else_%d:' % label_id)
        self.tab_push()

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

        self.tab_pop()
        self.generate('endif_%d:' % label_id)

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

        label_id = self.get_label_id()
        self.generate('loop_%d:' % label_id)
        self.tab_push()

        self._parse_expression()
        self._match('symbol', ')')

        expr_reg = self.get_reg(inc=False)
        self.generate('if (!R[%d]) goto endloop_%d;' % (expr_reg, label_id))

        while not self._accept('keyword', 'end'):
            try:
                self._parse_statement()
            except ParserError:
                self._resync_at_token('symbol', ';')

            self._match('symbol', ';')

        self._match('keyword', 'for')

        self.generate('goto loop_%d;' % label_id)
        self.tab_pop()
        self.generate('endloop_%d:' % label_id)

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

        out_names = []

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
            (num_args, out_names) = self._parse_argument_list(id.params)

            # Make sure that too few arguments are not used
            if num_args < len(id.params):
                self._runtime_error(('procedure call accepts %d argument(s),' +
                        ' %d given') % (len(id.params), num_args), id_line)
                raise ParserRuntimeError()

        self._match('symbol', ')')

        # Save the FP to the stack. Set next FP to return address
        self.comment('Setting caller FP', self.debug)
        self.generate('R[SP] = R[SP] - 1;')
        self.generate('MM[R[SP]] = R[FP];')
        self.comment('Setting return addr (current FP)', self.debug)
        self.generate('R[SP] = R[SP] - 1;')
        self.generate('R[FP] = R[SP];')

        # Generate a new call number so multiple calls do not cause collisions
        call_number = self.get_unique_call_id()

        # Push the return addr onto the stack
        self.generate('MM[R[SP]] = (int)&&%s_%d_%d;' %
                (id.name, id.mm_ptr, call_number))
                
        # Make the jump to the function call
        self.generate('goto %s_%d;' % (id.name, id.mm_ptr))

        # Generate the return label
        self.generate('%s_%d_%d:' % (id.name, id.mm_ptr, call_number))

        # The SP now points to the return address. Restore the old FP
        self.comment('Restore caller FP', self.debug)
        self.generate('R[SP] = R[SP] + 1;')
        self.generate('R[FP] = MM[R[SP]];')

        # Pop parameters off the stack
        for index, param in enumerate(id.params):
            out_name = out_names[index]

            self.comment('Popping \'%s\' param off the stack' % param.id.name,
                    self.debug)
                    
            size = param.id.size if param.id.size is not None else 1

            for index in range(size):
                # Move to the next memory space
                self.generate('R[SP] = R[SP] + 1;')

                if param.direction == 'out':
                    out_id = self._ids.find(out_name)

                    if self._ids.is_global(out_name):
                        self.generate('MM[%d] = MM[R[SP]];' % out_id.mm_ptr)
                    else:
                        self.generate('MM[R[FP]-%d] = MM[R[SP]];' % out_id.mm_ptr)

        self.comment('Move to caller local stack', self.debug)
        self.generate('R[SP] = R[SP] + 1;')

        return

    def _parse_argument_list(self, params, index=0, out_names=[]):
        """<argument_list> (Protected)

        Parses <argument_list> language structure.

            <argument_list> ::=
                <expression> ',' <argument_list> |
                <expression>

        Arguments:
            params: A list of Parameter namedtuple objects allowed in the
                procedure call.
            index: The index in params with which to match the found param.
                (Default: 0)
            out_names: A list of identifier names that are being used in this
                procedure call and must be written back.

        Returns:
            A tuple (index, out_names) consisting of the number of arguments
            encountered and a list of the identifiers used to write back.
        """
        line = self._current.line
        arg_type = None

        # Make sure that too many arguments are not used
        if index > len(params) - 1:
            self._runtime_error('procedure call accepts only %d argument(s)' %
                    len(params), line)
            raise ParserRuntimeError()

        param = params[index]

        if param.direction == 'out':
            arg_type = self._parse_name()

            # Save the identifier name so we know where to write the value
            out_names.append(self._previous.value)
        elif param.direction == 'in':
            arg_type = self._parse_expression()
            out_names.append(None)

        # Get the last reg assignment in the expr. This is argument's register
        expr_reg = self.get_reg(inc=False)

        if arg_type != param.id.type:
            self._type_error(param.id.type, arg_type, line)

        index += 1

        if self._accept('symbol', ','):
            (index, out_names) = self._parse_argument_list(params, index,
                    out_names)

        # Push the parameters onto the stack in reverse order. The last param
        # will reach this point first
        self.comment('Pushing argument onto the stack', self.debug)

        if param.id.size is not None:
            self.generate('R[SP] = R[SP] - %d;' % param.id.size)
        else:
            self.generate('R[SP] = R[SP] - 1;')

        self.generate('MM[R[SP]] = R[%d];' % expr_reg)

        return (index, out_names)

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
        elif id.size is not None:
            self._runtime_error('%s: array requires index' % id_name, id_line)

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
        self.comment('Parsing expression', self.debug)

        negate = False

        # Holds the register number of the expression result
        result = 0

        if self._accept('keyword', 'not'):
            negate = True

        line = self._current.line
        type = self._parse_arith_op()

        if negate and type not in ['integer', 'bool']:
            self._type_error('integer or bool', type, line)
            raise ParserTypeError()

        while True:
            operand1 = self.get_reg(inc=False)

            operation = ''
            if self._accept('symbol', '&'):
                operation = '&'
            elif self._accept('symbol', '|'):
                operation = '|'
            else:
                break

            if type not in ['integer', 'bool']:
                self._type_error('integer or bool', type, line)
                raise ParserTypeError()

            next_type = self._parse_arith_op()

            operand2 = self.get_reg(inc=False)

            if next_type not in ['integer', 'bool']:
                self._type_error('integer or bool', next_type, line)
                raise ParserTypeError()

            result = self.do_operation(operand1, type, operand2, next_type,
                    operation)

            if negate:
                self.generate('R[%d] = ~R[%d];' % (result, result))

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
            operand1 = self.get_reg(inc=False)

            operation = ''
            if self._accept('symbol', '+'):
                operation = '+'
            elif self._accept('symbol', '-'):
                operation = '-'
            else:
                break

            if type not in ['integer', 'float']:
                self._type_error('integer or float', type, line)
                raise ParserTypeError()

            next_type = self._parse_relation()

            operand2 = self.get_reg(inc=False)
            
            if next_type not in ['integer', 'float']:
                self._type_error('integer or float', next_type, line)
                raise ParserTypeError()

            self.do_operation(operand1, type, operand2, next_type, operation)

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
            operand1 = self.get_reg(inc=False)

            operation = ''
            if self._accept('symbol', '<'):
                operation = '<'
            elif self._accept('symbol', '>'):
                operation = '>'
            elif self._accept('symbol', '<='):
                operation = '<='
            elif self._accept('symbol', '>='):
                operation = '>='
            elif self._accept('symbol', '=='):
                operation = '=='
            elif self._accept('symbol', '!='):
                operation = '!='
            else:
                break

            if type not in ['integer', 'bool']:
                self._type_error('integer or bool', type, line)
                raise ParserTypeError()

            next_type = self._parse_term()

            operand2 = self.get_reg(inc=False)

            if next_type not in ['integer', 'bool']:
                self._type_error('integer or bool', next_type, line)
                raise ParserTypeError()

            self.do_operation(operand1, type, operand2, next_type, operation)

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
            operand1 = self.get_reg(inc=False)

            operation = ''
            if self._accept('symbol', '*'):
                operation = '*'
            elif self._accept('symbol', '/'):
                operation = '/'
            else:
                break

            if type not in ['integer', 'float']:
                self._type_error('integer or float', type, line)
                raise ParserTypeError()

            line = self._current.line
            next_type = self._parse_factor()

            operand2 = self.get_reg(inc=False)

            if next_type not in ['integer', 'float']:
                self._type_error('integer or float', next_type, line)
                raise ParserTypeError()

            self.do_operation(operand1, type, operand2, next_type, operation)

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
        line = self._current.line

        if self._accept('symbol', '('):
            type = self._parse_expression()
            self._match('symbol', ')')
        elif self._accept('string'):
            type = 'string'
            str_val = self._previous.value

            self.generate('R[%d] = (int)"%s";' % (self.get_reg(), str_val))
        elif self._accept('keyword', 'true'):
            type = 'bool'

            self.generate('R[%d] = 1;' % (self.get_reg()))
        elif self._accept('keyword', 'false'):
            type = 'bool'

            self.generate('R[%d] = 0;' % (self.get_reg()))
        elif self._accept('symbol', '-'):
            if self._first_name():
                type = self._parse_name()
            elif self._check('integer') or self._check('float'):
                type = self._parse_number(negate=True)
            else:
                self._syntax_error('variable name, integer, or float')
        elif self._first_name():
            type = self._parse_name()
        elif self._check('integer') or self._check('float'):
            type = self._parse_number(negate=False)
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
        elif id.size is not None:
            self._runtime_error('%s: array requires index' % id_name, id_line)

        # Generate code for the identifier encountered
        index_reg = self.get_reg(inc=False)

        # Get a register to store the address calculations
        id_reg = self.get_reg()

        # If identifier is param, mm_ptr will be the parameter offset
        # If identifier is local, mm_ptr will be the local offset
        # If identifier is global, mm_ptr is the direct memory space
        self.generate('R[%d] = %d;' % (id_reg, id.mm_ptr))

        if id.size is not None:
            self.generate('R[%d] = R[%d] + R[%d];' %
                    (id_reg, id_reg, index_reg))

        if self._ids.is_param(id.name):
            # Make sure that this is an 'in' parameter only
            direction = self._ids.get_param_direction(id.name)
            if direction != 'in':
                self._type_error('\'in\' param',
                        '\'%s\' param' % direction, line)
                raise ParserTypeError()

            # Calculate the parameter location
            self.comment('Param referenced', self.debug)
            self.generate('R[%d] = R[FP] + 1 + R[%d];' % (id_reg, id_reg))
        elif not self._ids.is_global(id.name):
            self.comment('Local var referenced', self.debug)
            self.generate('R[%d] = R[FP] - R[%d];' % (id_reg, id_reg))
        else:
            self.comment('Global var referenced', self.debug)

        self.generate('R[%d] = MM[R[%d]];' % (id_reg, id_reg))

        return id_type

    def _parse_number(self, negate=False):
        """Parse Number (Protected)

        Parses the <number> language structure.

            <number> ::=
                [0-9][0-9_]*[.[0-9_]*]

        Arguments:
            negate: Determines if the number should be negated or not.
        Returns:
            The type of the parsed number.
        """
        number = self._current.value
        type = self._current.type

        if not self._accept('integer') and not self._accept('float'):
            self._syntax_error('number')

        reg = self.get_reg()

        if type == 'integer':
            if negate:
                self.generate('R[%d] = -%s;' % (reg, number))
            else:
                self.generate('R[%d] = %s;' % (reg, number))
        else:
            if negate:
                self.generate('R_FLOAT_1 = -%s;' % number)
            else:
                self.generate('R_FLOAT_1 = %s;' % number)

            self.generate('memcpy(&R[%d], &R_FLOAT_1, sizeof(float));' % reg)

        return type
