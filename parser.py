#!/usr/bin/env python3

from scanner import Scanner

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
        self.token = None
        self.debug = debug

        # A flag used to undo a token get
        self._revert = False

        # A flag used to denote fatal parsing errors and stop any extraneous
        # output from the parser
        self._fatal_error = False


    def next_token(self):
        """Next Token

        Gets the next token from the inherited Scanner class. If revert flag
        is set, the previously encountered token will be served.
        """
        if self._revert:
            self._revert = False
        else:
            self.token = self._next_token()

        return


    def revert_token(self):
        """Revert Token

        When called, the next token received from the 'next_token()' function
        will be the previous token encountered. This is used to backtrack.
        """
        self._revert = True
        return


    def parse(self, src_path):
        """Parse Source File

        Begins the parse of the inputted source file.

        Arguments:
            src_path: The input source file to parse.

        Returns:
            True on success, False otherwise.
        """
        self._attach_file(src_path)

        return self.__consume_program()


    def _parse_msg(self, expected, prefix='Error'):
        """Print Parser Message (Protected)

        Prints a parser error message with details about the expected token
        and the current token being parsed.

        Arguments:
            expected: A string containing the expected token type/value.
            prefix: A string showing the level of error encountered. If the
                default string ('Error') is used, a fatal error will be
                reported and all future output will be silenced.
        """
        if self._fatal_error: return

        print(prefix.title(), ': ', sep='', end='')
        print('\"{0}\", line {1}'.format(self._src_path, self.token.line))
        print('    Expected {0}, '.format(expected), end='')
        print('encountered \"{0}\" ({1})'.format(self.token.value, self.token.type))
        print('    {0}'.format(self._get_line(self.token.line)))

        if prefix == 'Error': self._fatal_error = True

        return


    def __consume_program(self):
        """Consume Program (Private)

        Consumes the <program> language structure.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <program_header>
        if not self.__consume_program_header():
            return False

        # Consume: <program_body>
        if not self.__consume_program_body():
            return False

        return True


    def __consume_program_header(self):
        """Consume Program Header (Private)

        Consumes the <program_header> language structure.

        Returns:
            True on successful parse, False otherwise.
        """
        self.next_token()

        # Consume: 'program'
        if not self.__consume_keyword('program'):
            self._parse_msg('\"program\"')
            return False

        self.next_token()

        # Consume: <identifier>
        if not self.__consume_identifier():
            self._parse_msg('\"identifier\"')
            return False

        self.next_token()

        # Consume: 'is'
        if not self.__consume_keyword('is'):
            self._parse_msg('\"is\"')
            return False

        return True


    def __consume_program_body(self):
        """Consume Program Body (Private)

        Consumes the <program_body> language structure.

        Returns:
            True on successful parse, False otherwise.
        """
        self.next_token()

        # Consume: 'begin'
        if self.__consume_keyword('begin'):
            pass
        else:
            # Consume: (<declaration>';')*
            while True:
                # Consume: <declaration>
                if not self.__consume_declaration(optional=True):
                    break

                self.next_token()

                # Consume: ';'
                if not self.__consume_symbol(';'):
                    self._parse_msg('\";\"')
                    return False

                self.next_token()

            # Consume: 'begin'
            if not self.__consume_keyword('begin'):
                self._parse_msg('\"begin\"')
                return False

        self.next_token()

        # Consume: 'end'
        if self.__consume_keyword('end'):
            pass
        else:
            # Consume: (<statement>';')*
            while True:
                # Consume: <statement>
                if not self.__consume_statement(optional=True):
                    break

                self.next_token()

                # Consume: ';'
                if not self.__consume_symbol(';'):
                    self._parse_msg('\";\"')
                    return False

                self.next_token()

            # Consume: 'end'
            if not self.__consume_keyword('end'):
                self._parse_msg('\"end\"')
                return False

        self.next_token()

        # Consume: 'program'
        if not self.__consume_keyword('program'):
            self._parse_msg('\"program\"')
            return False

        return True


    def __consume_declaration(self, optional=False):
        """Consume Declaration (Private)

        Consumes the <declaration> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: ['global']
        if self.__consume_keyword('global'):
            self.next_token()

        # Consume: <procedure_declaration>
        if self.__consume_procedure_declaration(optional):
            pass
        # Consume: <variable_declaration>
        elif self.__consume_variable_declaration(optional):
            pass
        else:
            return False

        return True


    def __consume_procedure_declaration(self, optional=False):
        """Consume Procedure Declaration (Private)

        Consumes the <procedure_declaration> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        #Consume: <procedure_header>
        if not self.__consume_procedure_header(optional):
            return False

        # Consume: <procedure_body>
        if not self.__consume_procedure_body():
            return False

        return True


    def __consume_procedure_header(self, optional=False):
        """Consume Procedure Header (Private)

        Consumes the <procedure_header> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: 'procedure'
        if not self.__consume_keyword('procedure'):
            if not optional: self._parse_msg('\"procedure\"')
            return False

        self.next_token()

        # Consume: <identifier>
        if not self.__consume_identifier():
            self._parse_msg('identifier')
            return False

        self.next_token()

        # Consume: '('
        if not self.__consume_symbol('('):
            self._parse_msg('(')
            return False

        self.next_token()

        # Consume: ')'
        if not self.__consume_symbol(')'):
            # Consume: [<parameter_list>]
            if not self.__consume_parameter_list():
                return False

            self.next_token()

            # Consume: ')'
            if not self.__consume_symbol(')'):
                return False

        return True


    def __consume_procedure_body(self):
        """Consume Procedure Body (Private)

        Consumes the <procedure_body> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        self.next_token()

        # Consume: 'begin'
        if self.__consume_keyword('begin'):
            pass
        else:
            # Consume: (<declaration>';')*
            while True:
                # Consume: <declaration>
                if not self.__consume_declaration(optional=True):
                    break

                self.next_token()

                # Consume: ';'
                if not self.__consume_symbol(';'):
                    self._parse_msg('\";\"')
                    return False

                self.next_token()

            # Consume: 'begin'
            if not self.__consume_keyword('begin'):
                self._parse_msg('\"begin\"')
                return False

        self.next_token()

        # Consume: 'end'
        if self.__consume_keyword('end'):
            pass
        else:
            # Consume: (<statement>';')*
            while True:
                # Consume: <statement>
                if not self.__consume_statement(optional=True):
                    break

                self.next_token()

                # Consume: ';'
                if not self.__consume_symbol(';'):
                    self._parse_msg('\";\"')
                    return False

                self.next_token()

            # Consume: 'end'
            if not self.__consume_keyword('end'):
                self._parse_msg('\"end\"')
                return False

        self.next_token()

        # Consume: 'program'
        if not self.__consume_keyword('procedure'):
            self._parse_msg('\"procedure\"')
            return False

        return True


    def __consume_parameter_list(self, optional=False):
        """Consume Parameter List (Private)

        Consumes the <parameter_list> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <parameter>
        if not self.__consume_parameter(optional):
            return False

        self.next_token()

        # Consume: ','
        if self.__consume_symbol(','):
            self.next_token()

            # Consume: <parameter_list>
            if not self.__consume_parameter_list():
                return False
        else:
            self.revert_token()

        return True


    def __consume_parameter(self, optional=False):
        """Consume Parameter (Private)

        Consumes the <parameter> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <variable_declaration>
        if not self.__consume_variable_declaration(optional):
            return False

        self.next_token()

        # Consume: 'in'
        if self.__consume_keyword('in'):
            pass
        # Consume: 'out'
        elif self.__consume_keyword('out'):
            pass
        else:
            self._parse_msg('\"in\" or \"out\"')
            return False

        return True


    def __consume_variable_declaration(self, optional=False):
        """Consume Variable Declaration (Private)

        Consumes the <variable_declaration> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <type_mark>
        if not self.__consume_type_mark(optional):
            return False

        self.next_token()
        
        # Consume: <identifier>
        if not self.__consume_identifier():
            self._parse_msg('identifier')
            return False

        self.next_token()

        # Consume: ['['<integer>']']
        if self.__consume_symbol('['):
            self.next_token()

            # Consume: <integer>
            if not self.__consume_literal('integer'):
                return False

            self.next_token()

            # Consume: ']'
            if not self.__consume_symbol(']'):
                return False
        else:
            self.revert_token()

        return True


    def __consume_type_mark(self, optional=False):
        """Consume Type Mark (Private)

        Consumes the <type_mark> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <integer>
        if self.__consume_keyword('integer'):
            pass
        # Consume: <float>
        elif self.__consume_keyword('float'):
            pass
        # Consume: <bool>
        elif self.__consume_keyword('bool'):
            pass
        # Consume: <string>
        elif self.__consume_keyword('string'):
            pass
        else:
            if not optional: self._parse_msg('variable type')
            return False

        return True


    def __consume_statement(self, optional=False):
        """Consume Statement (Private)

        Consumes the <statement> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <assignment_statement>
        if self.__consume_assignment_statement(optional):
            pass
        # Consume: <if_statement>
        elif self.__consume_if_statement(optional):
            pass
        # Consume: <loop_statement>
        elif self.__consume_loop_statement(optional):
            pass
        # Consume: <return_statement>
        elif self.__consume_keyword('return'):
            pass
        else:
            return False

        return True


    def __consume_assignment_statement(self, optional=False):
        """Consume Assignment Statement (Private)

        Consumes the <assignment_statement> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <destination>
        if not self.__consume_destination(optional):
            return False

        self.next_token()

        # Consume: ':='
        if not self.__consume_symbol(':='):
            self._parse_msg('\":=\"')
            return False

        self.next_token()

        # Consume: <expression>
        if not self.__consume_expression():
            return False

        return True


    def __consume_if_statement(self, optional=False):
        """Consume If Statement (Private)

        Consumes the <if_statement> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        pass


    def __consume_loop_statement(self, optional=False):
        """Consume Loop Statement (Private)

        Consumes the <loop_statement> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        pass


    # TODO: Destination and Name are the same. Is this right?
    def __consume_destination(self, optional=False):
        """Consume Destination (Private)

        Consumes the <destination> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <identifier>
        if not self.__consume_identifier():
            if not optional: self._parse_msg('identifier')
            return False

        self.next_token()

        # Consume: '['
        if self.__consume_symbol('['):
            self.next_token()

            # Consume: <expression>
            if not self.__consume_expression():
                return False

            self.next_token()

            # Consume: ']'
            if not self.__consume_symbol(']'):
                self._parse_msg('\"]\"')
                return False
        else:
            self.revert_token()

        return True


    def __consume_expression(self, optional=False):
        """Consume Expression (Private)

        Consumes the <expression> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: 'not'
        if self.__consume_keyword('not'):
            self.next_token()

            # Consume: <arith_op>
            if not self.__consume_arith_op():
                return False
        # Consume: <arith_op>
        elif self.__consume_arith_op(optional=True):
            pass
        else:
            # Consume: <expression>
            if not self.__consume_expression():
                return False

            self.next_token()

            # Consume: '&' or '|'
            if not self.__consume_symbol('&') and \
                    not self.__consume_symbol('|'):
                self._parse_msg('\"&\" or \"|\"')
                return False

            self.next_token()

            # Consume: <arith_op>
            if not self.__consume_arith_op():
                return False

        return True


    # TODO: The recursion in this function breaks it. Fix this.
    def __consume_arith_op(self, optional=False):
        """Consume Arithmetic Operator (Private)

        Consumes the <arith_op> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <relation>
        if self.__consume_relation(optional):
            pass
        # Consume: <arith_op>
        elif self.__consume_arith_op():
            # Consume: '+' or '-'
            if not self.__consume_symbol('+') and \
                    not self.__consume_symbol('-'):
                self._parse_msg('\"+\" or \"-\"')
                return False

            self.next_token()

            # Consume: <relation>
            if not self.__consume_relation():
                return False

        return True


    # TODO: The recursion in this function breaks it. Fix this.
    def __consume_relation(self, optional=False):
        """Consume Relation (Private)

        Consumes the <relation> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <term>
        if self.__consume_term(optional):
            pass
        # Consume: <relation>
        elif self.__consume_relation():
            # Consume: '<' or '>=' or '<=' or '>' or '==' or '!='
            if not self.__consume_symbol('<') and \
                    not self.__consume_symbol('>=') and \
                    not self.__consume_symbol('<=') and \
                    not self.__consume_symbol('>') and \
                    not self.__consume_symbol('==') and \
                    not self.__consume_symbol('!='):
                self.parse_msg('relational operator')
                return False

            self.next_token()

            # Consume: <term>
            if not self.__consume_term():
                return False

        return True


    # TODO: The recursion in this function breaks it. Fix this.
    def __consume_term(self, optional=False):
        """Consume Term (Private)

        Consumes the <term> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <factor>
        if self.__consume_factor(optional):
            pass
        # Consume: <term>
        elif self.__consume_term():
            self.next_token()

            # Consume: '*' or '/'
            if not self.__consume_symbol('*') and \
                    not self.__consume_symbol('/'):
                self.parse_msg('\"*\" or \"/\"')
                return False

            self.next_token()

            # Consume: <factor>
            if not self.__consume_factor():
                return False

        return True
    

    def __consume_factor(self, optional=False):
        """Consume Factor (Private)

        Consumes the <factor> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: '('
        if self.__consume_symbol('('):
            self.next_token()

            # Consume: <expression>
            if not self.__consume_expression():
                return False

            self.next_token()

            # Consume: ')'
            if not self.__consume_symbol(')'):
                return False
        # Consume: <procedure_call>
        elif self.__consume_procedure_call(optional):
            pass
        # Consume: <name>
        elif self.__consume_name(optional):
            pass
        # Consume: <string>
        elif self.__consume_literal('string') or \
                self.__consume_literal('integer') or \
                self.__consume_literal('float'):
            pass
        # Consume: <true> | <false>
        elif self.__consume_keyword('true') or self.__consume_keyword('false'):
            pass
        # Consume: ['-'] <name> | <integer> | <float>
        elif self.__consume_symbol('-'):
            self.next_token()

            # Consume: <name> or 'integer' or 'float'
            if not self.__consume_name() and \
                    not self.__consume_literal('integer') and \
                    not self.__consume_literal('float'):
                self._parse_msg('name or number')
                return False
        else:
            if not optional: self._parse_msg('valid factor')
            return False

        return True


    def __consume_procedure_call(self, optional=False):
        """Consume Procedure Call (Private)

        Consumes the <procedure_call> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <identifier>
        if not self.__consume_identifier():
            if not optional: self._parse_msg('identifier')
            return False

        self.next_token()

        # Consume: '('
        if not self.__consume_symbol('('):
            self._parse_msg('(')
            return False

        self.next_token()

        # Consume: ')'
        if not self.__consume_symbol(')'):
            # Consume: [<argument_list>]
            if not self.__consume_argument_list():
                return False

            self.next_token()

            # Consume: ')'
            if not self.__consume_symbol(')'):
                return False

        return True
            

    def __consume_name(self, optional=False):
        """Consume Name (Private)

        Consumes the <name> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <identifier>
        if not self.__consume_identifier():
            if not optional: self._parse_msg('identifier')
            return False

        self.next_token()

        # Consume: '['
        if self.__consume_symbol('['):
            self.next_token()

            # Consume: <expression>
            if not self.__consume_expression():
                return False

            self.next_token()

            # Consume: ']'
            if not self.__consume_symbol(']'):
                self._parse_msg('\"]\"')
                return False
        else:
            self.revert_token()

        return True


    def __consume_argument_list(self, optional=False):
        """Consume Argument List (Private)

        Consumes the <argument_list> language structure.

        Arguments:
            optional: If True, the first fatal error encountered will
                be ignored. Defaults to False.

        Returns:
            True on successful parse, False otherwise.
        """
        # Consume: <expression>
        if not self.__consume_expression(optional):
            return False

        self.next_token()

        # Consume: ','
        if self.__consume_symbol(','):
            self.next_token()

            # Consume: <argument_list>
            if not self.__consume_argument_list():
                return False
        else:
            self.revert_token()

        return True


    def __consume_keyword(self, expected_keyword):
        """Consume Keyword (Private)

        Consumes the any valid keyword of the language.

        Arguments:
            expected_keyword: A string denoting the keyword expected.

        Returns:
            True on successful parse, False otherwise.
        """
        if self.token.type != 'keyword' or self.token.value != expected_keyword:
            return False

        if self.debug: print(self.token)
        return True


    def __consume_identifier(self):
        """Consume Identifier (Private)

        Consumes the any valid identifier encountered.

        Returns:
            True on successful parse, False otherwise.
        """
        if self.token.type != 'identifier':
            return False

        if self.debug: print(self.token)
        return True


    def __consume_symbol(self, expected_symbol):
        """Consume Identifier (Private)

        Consumes the any valid symbol of the language.

        Arguments:
            expected_symbol: A string denoting the symbol expected.

        Returns:
            True on successful parse, False otherwise.
        """
        if self.token.type != 'symbol' or self.token.value != expected_symbol:
            return False

        if self.debug: print(self.token)
        return True


    def __consume_literal(self, literal_type):
        """Consume Identifier (Private)

        Consumes the any valid symbol of the language.

        Arguments:
            literal_type: A string denoting the literal type expected.

        Returns:
            True on successful parse, False otherwise.
        """

        if self.token.type != literal_type:
            return False

        if self.debug: print(self.token)
        return True

