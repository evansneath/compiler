#!/usr/bin/env python3

from scanner import Scanner

class Parser(Scanner):


    def __init__(self):
        super(Parser, self).__init__()


    def parse(self, src_path):
        self._attach_file(src_path)

        if self.__consume_program():
            print('Success')
        else:
            print('Failure')

        return


    def _parse_msg(self, expected, token, prefix='Error'):
        print(prefix.title(), ': ', sep='', end='')
        print('\"{0}\", line {1}'.format(self._src_path, token.line))
        print('    Expected \"{0}\", '.format(expected), end='')
        print('encountered \"{0}\" ({1})'.format(token.value, token.type))
        print('    {0}'.format(self._get_line(token.line)))

        return


    def __consume_program(self):
        if not self.__consume_program_header():
            return False

        if not self.__consume_program_body():
            return False

        return True


    def __consume_program_header(self):
        if not self.__consume_keyword('program'):
            return False

        if not self.__consume_identifier():
            return False

        if not self.__consume_keyword('is'):
            return False

        return True


    def __consume_program_body(self):
        while True:
            #if not self.__consume_declaration():
            #    return False

            if not self.__consume_symbol(';'):
                return False

        if not self.__consume_keyword('begin'):
            return False

        while True:
            #if not self.__consume_statement():
            #    return False

            if not self.__consume_symbol(';'):
                return False

        if not self.__consume_identifier('end'):
            return False

        if not self.__consume_identifier('program'):
            return False

        return True


    def __consume_keyword(self, expected_keyword):
        token = self._next_token()

        if token.type != 'keyword' or token.value != expected_keyword:
            self._parse_msg(expected_keyword, token)
            return False

        print(token.value)
        return True


    def __consume_identifier(self):
        token = self._next_token()

        if token.type != 'identifier':
            self._parse_msg('identifier', token)
            return False

        print(token.value)
        return True


    def __consume_symbol(self, expected_symbol):
        token = self._next_token()

        if token.type != 'symbol' or token.value != expected_symbol:
            self._parse_msg(expected_symbol, token)
            return False

        print(token.value)
        return True


    def __scan_test(self):
        # Print every token until we hit the end of file or an error
        while True:
            token = self._next_token()
            print(token)

            if token.type in ['eof', 'error']:
                break

        return

