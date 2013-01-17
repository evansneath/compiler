#!/usr/bin/env python3

"""
File:       scanner.py
Author:     Evan Sneath
"""

from collections import namedtuple
import os


class Scanner(object):
    """Scanner class

    This class implements a scanner object to scan a source code file in the
    compilation process.
    """

    # Create a named tuple object factory for tokens
    Token = namedtuple('Token', ['type', 'value', 'line'])

    # Define an empty identifier (symbol) table for use in the scanner
    identifiers = {}

    # Create a keyword list for the scanner
    keywords = [
        'string', 'int', 'bool', 'float', 'global', 'in', 'out', 'if', 'then',
        'else', 'case', 'for', 'and', 'or', 'not', 'program', 'procedure',
        'begin', 'return', 'end',
    ]

    symbols = [
        ':', ';', ',', '+', '-', '*', '/', '(', ')', '<', '<=', '>', '>=',
        '!=', '=', ':=', '{', '}',
    ]

    # More for personal reference, but might be useful
    token_types = [
        'keyword',
        'symbol',
        'identifier',
        'string',
        'int',
        'bool',
        'float',
    ]


    def __init__(self):
        super(Scanner, self).__init__()

        # Holds all source file data (code) to be scanned
        self.src = None

        # Holds the location of the next character to scan in the source file
        self.line_pos = 0
        self.char_pos = 0

        # Initialize the symbol table with each keyword
        for keyword in self.keywords:
            self.identifiers[keyword] = self.Token('keyword', keyword, None)


    def attach_file(self, src_path):
        """Attach file

        Attach a file to the scanner and prepare for token collection.

        Arguments:
            source_path: The path to the source file to scan.

        Returns:
            True on success, False otherwise.
        """
        # Make sure the inputted file is a actual file
        if not os.path.isfile(src_path):
            print('Error: Inputted path is not a file')
            return False

        # Try to read all data from the file and split each line into a list
        # element for easy access to line numbers (keep line endings)
        try:
            with open(src_path) as f:
                self.src = f.read().splitlines(True)
        except IOError:
            print('Error: Could not read inputted file')
            return False

        return True

    def next_token(self):
        """Scan For Next Token

        Scans the source code for the next token. The next token is then
        returned for parsing.

        Returns:
            The next token object in the source code.
        """
        value = ''
        value_type = None

        # Get the first character, this can narrow down the type of the token
        if self._skip_spaces() == 'eof':
            return self.Token('eof', None, self.line_pos+1)

        char = self.src[self.line_pos][self.char_pos]

        if char == '\"':
            # We know this is a string. Find the next quotation and return it
            string_end = self.src[self.line_pos].find('\"', self.char_pos+1)

            if string_end != -1:
                value = self.src[self.line_pos][self.char_pos+1:string_end]

                for index, char in enumerate(value):
                    if not char.isalnum() and char not in ' _,;:.\'':
                        value[index] = ' '
                        print('Error: Invalid character in string (%s), ' + \
                            'line %s', value, self.line_pos+1)

                self.char_pos += len(value) + 2

                return self.Token('string', value, self.line_pos+1)
            else:
                print('Error: No string end quotation, line %s', self.line_pos+1)
                return False

        while True:
            valid = False

            # Check to see if the value is a comment
            if value + char == '//':
                # Skip to the newline
                self.char_pos = len(self.src[self.line_pos]) - 1

                # Get the next valid character and continue the scan
                if self._skip_spaces() == 'eof':
                    return self.Token('eof', None, self.line_pos+1)

                value = ''
                char = self.src[self.line_pos][self.char_pos]

                continue

            # Check to see if the value is a symbol
            if self._valid_symbol(value+char):
                valid = valid or True
                value_type = 'symbol'

            # Check to see if the value is an identifier
            if self._valid_identifier(value+char):
                valid = valid or True
                value_type = 'identifier'

                # Check to see if it's a keyword
                if value + char in self.keywords:
                    value_type = 'keyword'

            # Check to see if the value is an integer
            if self._valid_int(value+char):
                valid = valid or True
                value_type = 'int'

            # Check to see if the value is a float
            if self._valid_float(value+char):
                valid = valid or True
                value_type = 'float'

            if valid:
                # Good so far, check the next character
                value = value + char
                self.char_pos += 1

                # Check to make sure we haven't hit a line ending
                if self.src[self.line_pos][self.char_pos] == '\n':
                    break
                else:
                    char = self.src[self.line_pos][self.char_pos]
            else:
                break

        # Let's stop here. Last char checked caused illegal identifier
        return self.Token(value_type, value, self.line_pos+1)


    def _valid_symbol(self, value):
        if value not in self.symbols:
            return False

        return True


    def _valid_identifier(self, value):
        # The first character can only be [a-zA-Z]
        if not value[0].isalpha():
            return False

        # Every following character may be only [a-zA-Z0-9_]
        for char in value[1::]:
            if not char.isalpha() and not char.isdigit() and char != '_':
                return False

        return True


    def _valid_int(self, value):
        if not value[0].isdigit():
            return False

        for char in value[1::]:
            if not char.isdigit() and char != '_':
                return False

        return True


    # TODO: Fix floating point parsing
    def _valid_float(self, value):
        if not value[0].isdigit():
            return False

        if value.count('.') != 1:
            return False

        decimal_index = value.index('.')

        for char in value[1:decimal_index]:
            if not char.isdigit() and char != '_':
                return False

        #for char in value[decimal_index+1:
        return True


    def _skip_spaces(self):
        # Find the next line if we hit a newline
        while self.src[self.line_pos][self.char_pos] == '\n':
            self.line_pos += 1
            self.char_pos = 0

            if self.line_pos == len(self.src):
                return 'eof'

        # Find the next non-space character
        while self.src[self.line_pos][self.char_pos].isspace():
            self.char_pos += 1
        
        return None

