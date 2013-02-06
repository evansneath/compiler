#!/usr/bin/env python3

from scanner import Scanner

class Parser(Scanner):
    """Parser class

    Parses the given source file using the defined language structure.
    """
    def __init__(self):
        super(Parser, self).__init__()

        self.token = None
        self._revert = False


    def next_token(self):
        if self._revert:
            self._revert = False
        else:
            self.token = self._next_token()

        return


    def revert_token(self):
        self._revert = True


    def parse(self, src_path):
        self._attach_file(src_path)

        if self.__consume_program():
            print('Success')
        else:
            print('Failure')

        return


    def _parse_msg(self, expected, prefix='Error'):
        print(prefix.title(), ': ', sep='', end='')
        print('\"{0}\", line {1}'.format(self._src_path, self.token.line))
        print('    Expected {0}, '.format(expected), end='')
        print('encountered \"{0}\" ({1})'.format(self.token.value, self.token.type))
        print('    {0}'.format(self._get_line(self.token.line)))

        return


    def __consume_program(self):
        if not self.__consume_program_header():
            return False

        if not self.__consume_program_body():
            return False

        return True


    def __consume_program_header(self):
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
        self.next_token()

        if self.__consume_keyword('begin'):
            pass
        else:
            # Consume: (<declaration>';')*
            while True:
                # Consume: <declaration>
                if not self.__consume_declaration():
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

        if self.__consume_keyword('end'):
            pass
        else:
            # Consume: (<statement>';')*
            while True:
                # Consume: <statement>
                if not self.__consume_statement():
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


    def __consume_declaration(self):
        # Consume: ['global']
        if self.__consume_keyword('global'):
            self.next_token()

        # Consume: <procedure_declaration>
        if self.__consume_procedure_declaration():
            pass
        # Consume: <variable_declaration>
        elif self.__consume_variable_declaration():
            pass
        else:
            return False

        return True


    def __consume_procedure_declaration(self):
        #Consume: <procedure_header>
        if not self.__consume_procedure_header():
            return False

        # Consume: <procedure_body>
        if not self.__consume_procedure_body():
            return False

        return True


    def __consume_procedure_header(self):
        # Consume: 'procedure'
        if not self.__consume_keyword('procedure'):
            self._parse_msg('\"procedure\"')
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
        self.next_token()

        if self.__consume_keyword('begin'):
            pass
        else:
            # Consume: (<declaration>';')*
            while True:
                # Consume: <declaration>
                if not self.__consume_declaration():
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

        if self.__consume_keyword('end'):
            pass
        else:
            # Consume: (<statement>';')*
            while True:
                # Consume: <statement>
                if not self.__consume_statement():
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


    def __consume_parameter_list(self):
        # Consume: <parameter>
        if not self.__consume_parameter():
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


    def __consume_parameter(self):
        if not self.__consume_variable_declaration():
            return False

        self.next_token()

        if self.__consume_keyword('in'):
            pass
        elif self.__consume_keyword('out'):
            pass
        else:
            self._parse_msg('\"in\" or \"out\"')
            return False

        return True


    def __consume_variable_declaration(self):
        # Consume: <type_mark>
        if not self.__consume_type_mark():
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


    def __consume_type_mark(self):
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
            self._parse_msg('variable type')
            return False

        return True


    def __consume_statement(self):
        # Consume: <assignment_statement>
        if self.__consume_assignment_statement():
            pass
        # Consume: <if_statement>
        elif self.__consume_if_statement():
            pass
        # Consume: <loop_statement>
        elif self.__consume_loop_statement():
            pass
        # Consume: <return_statement>
        elif self.__consume_keyword('return'):
            pass
        else:
            return False

        return True


    def __consume_assignment_statement(self):
        if not self.__consume_destination():
            return False

        self.next_token()

        if not self.__consume_symbol(':='):
            self._parse_msg('\":=\"')
            return False

        self.next_token()

        if not self.__consume_expression():
            return False

        return True


    def __consume_if_statement(self):
        pass


    def __consume_loop_statement(self):
        pass


    def __consume_return_statement(self):
        pass


    # TODO: Destination and Name are the same. Is this right?
    def __consume_destination(self):
        if not self.__consume_identifier():
            self._parse_msg('identifier')
            return False

        self.next_token()

        if self.__consume_symbol('['):
            self.next_token()

            if not self.__consume_expression():
                return False

            self.next_token()

            if not self.__consume_symbol(']'):
                self._parse_msg('\"]\"')
                return False
        else:
            self.revert_token()

        return True


    def __consume_expression(self):
        if self.__consume_keyword('not'):
            self.next_token()

            if not self.__consume_arith_op():
                return False
        elif self.__consume_arith_op():
            pass
        else:
            if not self.__consume_expression():
                return False

            self.next_token()

            if not self.__consume_symbol('&') and not self.__consume_symbol('|'):
                self._parse_msg('\"&\" or \"|\"')
                return False

            self.next_token()

            if not self.__consume_arith_op():
                return False

        return True


    def __consume_arith_op(self):
        if self.__consume_relation():
            pass
        # Consume: <arith_op>
        elif self.__consume_arith_op():
            # Consume: '+' or '-'
            if not self.__consume_symbol('+') and not self.__consume_symbol('-'):
                self._parse_msg('\"+\" or \"-\"')
                return False

            self.next_token()

            # Consume: <relation>
            if not self.__consume_relation():
                return False

        return True


    def __consume_relation(self):
        if self.__consume_term():
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


    def __consume_term(self):
        if self.__consume_factor():
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

            if not self.__consume_factor():
                return False

        return True
    

    def __consume_factor(self):
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
        elif self.__consume_procedure_call():
            pass
        # Consume: <string>
        elif self.__consume_literal('string'):
            pass
        # Consume: <true> | <false>
        elif self.__consume_keyword('true') or self.__consume_keyword('false'):
            pass
        # Consume: ['-'] <name> | <integer> | <float>
        elif self.__consume_symbol('-'):
            self.next_token()

            if not self.__consume_name() and \
                    not self.__consume_literal('integer') and \
                    not self.__consume_literal('float'):
                self._parse_msg('name or number')
                return False
        else:
            self._parse_msg('valid factor')
            return False

        return True


    def __consume_procedure_call(self):
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
            # Consume: [<argument_list>]
            if not self.__consume_argument_list():
                return False

            self.next_token()

            # Consume: ')'
            if not self.__consume_symbol(')'):
                return False

        return True
            

    def __consume_name(self):
        if not self.__consume_identifier():
            self._parse_msg('identifier')
            return False

        self.next_token()

        if self.__consume_symbol('['):
            self.next_token()

            if not self.__consume_expression():
                return False

            self.next_token()

            if not self.__consume_symbol(']'):
                self._parse_msg('\"]\"')
                return False
        else:
            self.revert_token()

        return True


    def __consume_argument_list(self):
        if not self.__consume_expression():
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
        if self.token.type != 'keyword' or self.token.value != expected_keyword:
            return False

        print(self.token)
        return True


    def __consume_identifier(self):
        if self.token.type != 'identifier':
            return False

        print(self.token)
        return True


    def __consume_symbol(self, expected_symbol):
        if self.token.type != 'symbol' or self.token.value != expected_symbol:
            return False

        print(self.token)
        return True


    def __consume_literal(self, literal_type):
        if self.token.type != literal_type:
            return False

        print(self.token)
        return True


    def __scan_test(self):
        # Print every token until we hit the end of file or an error
        while True:
            self.next_token()
            print(self.token)

            if self.token.type in ['eof', 'error']:
                break

        return

