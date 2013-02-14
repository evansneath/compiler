#!/usr/bin/env python3

"""Scanner module

With any attached file, the Scanner class will scan the file token-by-token
until an end-of-file is encountered.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    Token: A named tuple object containing token information.
    Scanner: An implementation of a scanner for the source language.
"""

from collections import namedtuple
import os


"""Create a named tuple object factory for tokens"""
Token = namedtuple('Token', ['type', 'value', 'line'])


class Scanner(object):
    """Scanner class

    This class implements a scanner object to scan a source code file in the
    compilation process. This class is designed to be subclassed to be used
    during the parsing stage of the compiler.

    Attributes:
        identifiers: An identifiers (symbol) table. All identifiers are stored
            in the dictionary with the identifier name as the key.
        keywords: A list of valid keywords in the language.
        symbols: A list of valid symbols in the language.

    Methods:
        attach_file: Binds a source file to the scanner to begin scanning.
        next_token: Returns the next token of the attached file. This token
            will be of the Token named tuple class.
    """
    # Define an empty identifier (symbol) table for use in the scanner
    identifiers = {}

    # Define all language keywords
    keywords = [
        'string', 'integer', 'bool', 'float', 'global', 'is', 'in', 'out',
        'if', 'then', 'else', 'for', 'and', 'or', 'not', 'program',
        'procedure', 'begin', 'return', 'end', 'true', 'false',
    ]

    # Define all language symbols
    symbols = [
        ':', ';', ',', '+', '-', '*', '/', '(', ')', '<', '<=', '>', '>=',
        '!=', '==', ':=', '[', ']', '&', '|',
    ]

    def __init__(self):
        super(Scanner, self).__init__()

        # Hold the file path of the attached source file
        self._src_path = ''

        # Holds all source file data (code) to be scanned
        self.__src = ''

        # Holds the location of the next character to scan in the source file
        self.__line_pos = 0
        self.__char_pos = 0

        # Initialize the symbol table with each keyword
        for keyword in self.keywords:
            self.identifiers[keyword] = Token('keyword', keyword, None)

    def attach_file(self, src_path):
        """Attach file

        Attach a file to the scanner and prepare for token collection.

        Arguments:
            src_path: The path to the source file to scan.

        Returns:
            True on success, False otherwise.
        """
        # Make sure the inputted file is a actual file
        if not os.path.isfile(src_path):
            print('Error: \"{0}\"'.format(src_path))
            print('    Inputted path is not a file')
            return False

        # Try to read all data from the file and split by line
        try:
            with open(src_path) as f:
                self.__src = f.read().splitlines(keepends=True)
        except IOError:
            print('Error: \"{0}\"'.format(src_path))
            print('    Could not read inputted file')
            return False

        # The file was attached and read successfully, store the path
        self._src_path = src_path

        return True

    def next_token(self):
        """Scan For Next Token

        Scans the source code for the next token. The next token is then
        returned for parsing.

        Returns:
            The next token object in the source code.
        """
        # Store the token type as it is discovered
        token_type = ''

        # Get the first character, narrow down the data type possiblilites
        char = self.__next_word()

        if char is None:
            return Token('eof', None, self.__line_pos)

        # Use the first character to choose the token type to expect
        if char == '\"':
            value, token_type = self.__expect_string()
        elif char.isdigit():
            value, token_type = self.__expect_number(char)
        elif char.isalpha():
            value, token_type = self.__expect_identifier(char)
        elif char in self.symbols:
            value, token_type = self.__expect_symbol(char)
        else:
            # We've run across a character that shouldn't be here
            msg = 'Invalid character \'{0}\' encountered'.format(char)
            self.__warning(msg, hl=self.__char_pos-1)

            # Run this function again until we find something good
            return self.next_token()

        if token_type == 'comment':
            # If we find a comment, get a token on the next line
            self.__next_line()
            return self.next_token()

        # Build the new token object
        new_token = Token(token_type, value, self.__line_pos+1)

        if token_type == 'identifier' and value not in self.identifiers:
            # Add any newly discovered identifiers to the identifiers table
            self.identifiers[value] = new_token

        return new_token

    def _get_line(self, line_number):
        """Get Line (Protected)

        Returns a line stripped of leading and trailing whitespace given a
        line number.

        Arguments:
            line_number: The line number of the attached source file to print.

        Returns:
            The requested line number from the source, None on invalid line.
        """
        if line_number > 0 and line_number <= len(self.__src):
            return self.__src[line_number-1].strip()

    def __warning(self, msg, hl=-1):
        """Print Scanner Warning Message (Private)

        Prints a formatted warning message.

        Arguments:
            msg: The warning message to display
            hl: If not -1, there will be an pointer (^) under a
                character in the line to be highlighted. (Default: -1)
        """
        line = self.__src[self.__line_pos][0:-1]

        print('Warning: "', self._src_path, '", ', sep='', end='')
        print('line ', self.__line_pos+1, sep='')
        print('    ', msg, '\n    ', line.strip(), sep='')

        if hl != -1:
            lspaces = line.find(line.strip()[0])
            print('    {0}^'.format(' '*(abs(hl)-lspaces)))

        return

    def __next_word(self):
        """Get Next Word Character (Private)

        Move the cursor to the start of the next non-space character in the
        file.

        Returns:
            The first non-space character encountered. None if the end of
            file was reached.
        """
        char = ''

        while True:
            char = self.__src[self.__line_pos][self.__char_pos]

            # React according to spaces and newlines
            if char == '\n':
                if not self.__next_line():
                    return None
            elif char in ' \t':
                self.__char_pos += 1
            else:
                break

        # Increment to the next character
        self.__char_pos += 1
        return char

    def __next_line(self):
        """Travel to Next Line (Private)

        Move the cursor to the start of the next line safely.

        Returns:
            True on success, False if end of file is encountered
        """
        self.__line_pos += 1
        self.__char_pos = 0

        # Check to make sure this isn't the end of file
        if self.__line_pos == len(self.__src):
            return False

        return True

    def __next_char(self, peek=False):
        """Get Next Character (Private)

        Move the cursor to the next character in the file.

        Arguments:
            peek: If True, the character position pointer will not be
                incremented. Set by default to False.

        Returns:
            The next character encountered. None if the end of line
            was reached.
        """
        # Get the next pointed character
        char = self.__src[self.__line_pos][self.__char_pos]

        # Return None if we hit a line ending
        if char == '\n':
            return None

        # Increment to the next character
        if not peek:
            self.__char_pos += 1

        return char

    def __expect_string(self):
        """Expect String Token (Private)

        Parses the following characters in hope of a valid string. If an
        invalid string is encountered, all attempts are made to make it valid.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will be 'string'.
        """
        value = ''
        hanging_quote = False

        # We know this is a string. Find the next quotation and return it
        string_end = self.__src[self.__line_pos].find('\"', self.__char_pos)

        # If we have a hanging quotation, assume quote ends at end of line
        if string_end == -1:
            hanging_quote = True
            string_end = len(self.__src[self.__line_pos]) - 1
            self.__warning('No closing quotation in string', hl=string_end)

        value = self.__src[self.__line_pos][self.__char_pos:string_end]

        # Check for illegal characters, send a warning if encountered
        for i, char in enumerate(value):
            if not char.isalnum() and char not in ' _,;:.\'':
                value = value.replace(char, ' ', 1)
                msg = 'Invalid character \'{0}\' in string'.format(char)
                self.__warning(msg, hl=self.__char_pos+i)

        self.__char_pos += len(value)
        if not hanging_quote:
            self.__char_pos += 1

        return value, 'string'

    def __expect_number(self, char):
        """Expect Number Token (Private)

        Parses the following characters in hope of a valid integer or float.

        Arguments:
            char: The first character already picked for the value.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will either be 'int' indicating a valid
            integer or 'float' indicating a valid floating point value.
        """
        value = '' + char
        token_type = 'integer'

        is_float = False

        while True:
            char = self.__next_char(peek=True)

            if char is None:
                break
            elif char == '.' and not is_float:
                # We found a decimal point. Move to float mode
                is_float = True
                token_type = 'float'
            elif not char.isdigit() and char != '_':
                break

            value += char
            self.__char_pos += 1

        # Remove all underscores in the int/float. These serve no purpose
        value = value.replace('_', '')

        # If nothing was given after the decimal point assume 0
        if is_float and value.split('.')[-1] == '':
            value += '0'

        return value, token_type

    def __expect_identifier(self, char):
        """Expect Identifier Token (Private)

        Parses the following characters in hope of a valid identifier.

        Arguments:
            char: The first character already picked for the value.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will either be 'identifier' indicating a
            valid identifier or 'keyword' indicating a valid keyword.
        """
        value = '' + char
        token_type = 'identifier'

        while True:
            char = self.__next_char(peek=True)

            if char is None:
                break
            elif not char.isalnum() and char != '_':
                break

            value += char
            self.__char_pos += 1

        if value in self.keywords:
            token_type = 'keyword'

        return value, token_type

    def __expect_symbol(self, char):
        """Expect Symbol Token (Private)

        Parses the following characters in hope of a valid symbol.

        Arguments:
            char: The first character already picked for the value.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will either be 'symbol' indicating a
            valid identifier or 'comment' indicating a comment until line end.
        """
        value = '' + char

        while True:
            char = self.__next_char(peek=True)

            if char is None:
                break
            elif value + char == '//':
                return None, 'comment'
            elif value + char not in self.symbols:
                break

            value += char
            self.__char_pos += 1

        return value, 'symbol'
