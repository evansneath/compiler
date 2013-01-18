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
        'begin', 'return', 'end', 'true', 'false',
    ]

    symbols = [
        ':', ';', ',', '+', '-', '*', '/', '(', ')', '<', '<=', '>', '>=',
        '!=', '=', ':=', '{', '}',
    ]

    # The following characters are allowed in strings along with alphanumberics
    string_characters = [
        '_', ',', ';', ':', '.', ',', '\''
    ]


    def __init__(self):
        super(Scanner, self).__init__()

        # Hold the file path of the attached source file
        self.src_path = None

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

        # The file was attached and read successfully, store the path
        self.src_path = src_path

        return True


    def print_msg(self, msg, prefix='Error', highlight=-1):
        """Print Scanner Message

        Prints a formatted message. Used for errors, warnings, or info.

        Arguments:
            msg: The main message to display
            prefix: The type of message. Defaults to 'Error'.
            highlight: If not -1, there will be an underscore under a
                character in the line to be highlighted.
        """
        print(prefix.title(), ': ', sep='', end='')
        print('\"{0}\", line {1}'.format(self.src_path, self.line_pos+1))
        print('    ', msg, sep='')
        print('    ', self.src[self.line_pos][0:-1].strip(), sep='')

        if highlight != -1:
            print('    {0}^'.format(' '*highlight))

        return


    def next_token(self):
        """Scan For Next Token

        Scans the source code for the next token. The next token is then
        returned for parsing.

        Returns:
            The next token object in the source code. None on irrecoverable
            error.
        """
        # Store the token type as it is discovered
        type = None

        # Get the first character, narrow down the data type possiblilites
        char = self._next_word()

        if char is None:
            return self.Token('eof', None, self.line_pos+1)

        # See if the token could be a string
        if char == '\"':
            value, type = self._expect_string(char)
        elif char.isdigit():
            value, type = self._expect_number(char)
        elif char.isalpha():
            value, type = self._expect_identifier(char)
        elif char in self.symbols:
            value, type = self._expect_symbol(char)
        else:
            # We've run across a character that should be here
            msg = 'Invalid character [{0}] encountered'.format(char)
            self.print_msg(msg, prefix='Warning')

            # Run this function again until we find something good
            return self.next_token()

        # Build the new token object
        token = self.Token(type, value, self.line_pos+1)

        # Add any newly discovered identifiers to the identifiers table
        if type == 'identifier' and value not in self.identifiers:
            self.identifiers[value] = token
        elif type == 'comment':
            # If we find a comment, get the next token instead
            return self.next_token()
        
        return token


    def _next_word(self):
        """Get Next Word Character (Protected)

        Move the cursor to the start of the next non-space character in the
        file.

        Returns:
            The first non-space character encountered. None if the end of
            file was reached.
        """
        char = ''

        while True:
            char = self.src[self.line_pos][self.char_pos]

            # React according to spaces and newlines
            if char == '\n':
                if not self._next_line():
                    return None
            elif char in ' \t':
                self.char_pos += 1
            else:
                break

        # Increment to the next character
        self.char_pos += 1
        return char


    def _next_line(self):
        """Travel to Next Line (Protected)

        Move the cursor to the start of the next line safely.

        Returns:
            True on success, False if end of file is encountered
        """
        self.line_pos += 1
        self.char_pos = 0

        # Check to make sure this isn't the end of file
        if self.line_pos == len(self.src):
            return False

        return True


    def _next_char(self, peek=False):
        """Get Next Character (Protected)

        Move the cursor to the next character in the file.

        Arguments:
            peek: If True, the character position pointer will not be
                incremented. Set by default to False.

        Returns:
            The next character encountered. None if the end of line
            was reached.
        """
        # Get the next pointed character
        char = self.src[self.line_pos][self.char_pos]

        # Return None if we hit a line ending
        if char == '\n':
            return None

        # Increment to the next character
        if not peek:
            self.char_pos += 1

        return char


    def _expect_string(self, char):
        """Expect String Token (Protected)

        Parses the following characters in hope for a valid string.

        Arguments:
            char: The first character already picked for the value.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will either be 'string' indicating a
            valid string or 'error' indicating a non-recoverable error.
        """
        value = ''

        # We know this is a string. Find the next quotation and return it
        string_end = self.src[self.line_pos].find('\"', self.char_pos)

        if string_end != -1:
            value = self.src[self.line_pos][self.char_pos:string_end]

            for i, char in enumerate(value):
                if not char.isalnum() and char not in ' _,;:.\'':
                    value = value.replace(char, ' ', 1)
                    msg = 'Invalid character [{0}] in string'.format(char)
                    self.print_msg(msg, prefix='Warning')
                        
            self.char_pos += len(value) + 1

            return value, 'string'
        else:
            self.print_msg('No closing quotation in string')
            return None, 'error'


    def _expect_number(self, char):
        """Expect Number Token (Protected)

        Parses the following characters in hope of a valid int or float.

        Arguments:
            char: The first character already picked for the value.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will either be 'int' indicating a valid
            integer or 'float' indicating a valid floating point value.
        """
        value = '' + char
        is_float = False
        float_digits = 0

        while True:
            char = self._next_char(peek=True)

            if char is None:
                break
            elif char == '.' and not is_float:
                # We found a decimal point. Move to float mode
                is_float = True
                float_digits -= 1
            elif not char.isdigit() and char != '_':
                break

            value += char
            self.char_pos += 1

            if is_float:
                float_digits += 1

        if not is_float:
            type = 'int'
        else:
            type = 'float'

            if float_digits == 0:
                # We have a decimal point but nothing after. Throw a warning
                msg = 'Digits missing after floating point decimal'
                self.print_msg(msg, prefix='Warning')

                # Fix this problem by assuming a 'x.0' floating point value
                value += '0'

        return value, type


    def _expect_identifier(self, char):
        """Expect Identifier Token (Protected)

        Parses the following characters in hope of a valid identifier.

        Arguments:
            char: The first character already picked for the value.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will either be 'identifier' indicating a
            valid identifier or 'keyword' indicating a valid keyword.
        """
        value = '' + char

        while True:
            char = self._next_char(peek=True)

            if char is None:
                break
            elif not char.isalnum() and char != '_':
                break

            # This is a valid character, commit to the value
            value += char
            self.char_pos += 1

        # Determine if this is an identifier or a keyword
        type = 'identifier'

        if value in self.keywords:
            type = 'keyword'

        return value, type


    def _expect_symbol(self, char):
        """Expect Symbol Token (Protected)

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
            char = self._next_char(peek=True)

            if char is None:
                break
            elif value + char == '//':
                # Check to see if this is a comment, if it is go to next line
                self._next_line()
                return None, 'comment'
            elif value + char not in self.symbols:
                # This is not a symbol. Stop here
                break
            
            # This is a valid character, commit to the value
            value += char
            self.char_pos += 1

        return value, 'symbol' 

