#!/usr/bin/env python3

"""Scanner module

With any attached file, the Scanner class will scan the file token-by-token
until an end-of-file is encountered.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    Scanner: An implementation of a scanner for the source language.
"""

from os.path import isfile

from lib.datatypes import Token


class Scanner:
    """Scanner class

    This class implements a scanner object to scan a source code file in the
    compilation process. This class is designed to be inherited to be used
    during the parsing stage of the compiler.

    Attributes:
        keywords: A list of valid keywords in the language.
        symbols: A list of valid symbols in the language.

    Methods:
        attach_source: Binds a source file to the scanner to begin scanning.
        next_token: Returns the next token of the attached file. This token
            will be of the Token named tuple class.
    """
    # Define all language keywords
    keywords = [
        'string', 'integer', 'bool', 'float', 'global', 'is', 'in', 'out',
        'if', 'then', 'else', 'for', 'and', 'or', 'not', 'program',
        'procedure', 'begin', 'return', 'end', 'true', 'false',
    ]

    # Define all language symbols
    symbols = [
        ':', ';', ',', '+', '-', '*', '/', '(', ')', '<', '<=', '>', '>=',
        '!', '!=', '=', '==', ':=', '[', ']', '&', '|',
    ]

    def __init__(self):
        super().__init__()

        # Holds the file path of the attached source file
        self._src_path = ''

        # Holds all source file data (code) to be scanned
        self._src = ''

        # Holds the location of the next character to scan in the source file
        self._line_pos = 0
        self._char_pos = 0

        return

    def attach_source(self, src_path):
        """Attach Source 

        Attach a source file to the scanner and prepare for token collection.

        Arguments:
            src_path: The path to the source file to scan.

        Returns:
            True on success, False otherwise.
        """
        # Make sure the inputted file is a actual file
        if not isfile(src_path):
            print('Error: "%s"' % src_path)
            print('    Inputted path is not a file')
            return False

        # Try to read all data from the file and split by line
        try:
            with open(src_path) as f:
                keepends = True
                self._src = f.read().splitlines(keepends)
        except IOError:
            print('Error: "%s"' % src_path)
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
        # Get the first character, narrow down the data type possibilities
        char = self._next_word()

        if char is None:
            return Token('eof', None, self._line_pos)

        # Use the first character to choose the token type to expect
        if char == '"':
            value, token_type = self._expect_string()
        elif char.isdigit():
            value, token_type = self._expect_number(char)
        elif char.isalpha():
            value, token_type = self._expect_identifier(char)
        elif char in self.symbols:
            value, token_type = self._expect_symbol(char)
        else:
            # We've run across a character that shouldn't be here
            msg = 'Invalid character \'%s\' encountered' % char
            self._scan_warning(msg, hl=self._char_pos-1)

            # Run this function again until we find something good
            return self.next_token()

        if token_type == 'comment':
            # If we find a comment, get a token on the next line
            self._next_line()
            return self.next_token()

        # Build the new token object
        new_token = Token(token_type, value, self._line_pos+1)

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
        if 0 < line_number <= len(self._src):
            return self._src[line_number-1].strip()

    def _scan_warning(self, msg, hl=-1):
        """Print Scanner Warning Message (Protected)

        Prints a formatted warning message.

        Arguments:
            msg: The warning message to display
            hl: If not -1, there will be an pointer (^) under a
                character in the line to be highlighted. (Default: -1)
        """
        line = self._src[self._line_pos][0:-1]

        print('Warning: "', self._src_path, '", ', sep='', end='')
        print('line ', self._line_pos+1, sep='')
        print('    ', msg, '\n    ', line.strip(), sep='')

        if hl != -1:
            left_spaces = line.find(line.strip()[0])
            print('    %s^' % (' '*(abs(hl)-left_spaces)))

        return

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
            char = self._src[self._line_pos][self._char_pos]

            # React according to spaces and newlines
            if char == '\n':
                if not self._next_line():
                    return None
            elif char in ' \t':
                self._char_pos += 1
            else:
                break

        # Increment to the next character
        self._char_pos += 1
        return char

    def _next_line(self):
        """Travel to Next Line (Protected)

        Move the cursor to the start of the next line safely.

        Returns:
            True on success, False if end of file is encountered
        """
        self._line_pos += 1
        self._char_pos = 0

        # Check to make sure this isn't the end of file
        if self._line_pos == len(self._src):
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
        char = self._src[self._line_pos][self._char_pos]

        # Return None if we hit a line ending
        if char == '\n':
            return None

        # Increment to the next character
        if not peek:
            self._char_pos += 1

        return char

    def _expect_string(self):
        """Expect String Token (Protected)

        Parses the following characters in hope of a valid string. If an
        invalid string is encountered, all attempts are made to make it valid.

        Returns:
            (value, token_type) - A tuple describing the final parsed token.
            The resulting token type will be 'string'.
        """
        hanging_quote = False

        # We know this is a string. Find the next quotation and return it
        string_end = self._src[self._line_pos].find('"', self._char_pos)

        # If we have a hanging quotation, assume quote ends at end of line
        if string_end == -1:
            hanging_quote = True
            string_end = len(self._src[self._line_pos]) - 1
            self._scan_warning('No closing quotation in string', hl=string_end)

        value = self._src[self._line_pos][self._char_pos:string_end]

        # Check for illegal characters, send a warning if encountered
        for i, char in enumerate(value):
            if not char.isalnum() and char not in ' _,;:.\'':
                value = value.replace(char, ' ', 1)
                msg = 'Invalid character \'%s\' in string' % char
                self._scan_warning(msg, hl=self._char_pos+i)

        self._char_pos += len(value)
        if not hanging_quote:
            self._char_pos += 1

        return value, 'string'

    def _expect_number(self, char):
        """Expect Number Token (Protected)

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
            char = self._next_char(peek=True)

            if char is None:
                break
            elif char == '.' and not is_float:
                # We found a decimal point. Move to float mode
                is_float = True
                token_type = 'float'
            elif not char.isdigit() and char != '_':
                break

            value += char
            self._char_pos += 1

        # Remove all underscores in the int/float. These serve no purpose
        value = value.replace('_', '')

        # If nothing was given after the decimal point assume 0
        if is_float and value.split('.')[-1] == '':
            value += '0'

        return value, token_type

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
        token_type = 'identifier'

        while True:
            char = self._next_char(peek=True)

            if char is None:
                break
            elif not char.isalnum() and char != '_':
                break

            value += char
            self._char_pos += 1

        if value in self.keywords:
            token_type = 'keyword'

        return value, token_type

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
            elif value + str(char) == '//':
                return None, 'comment'
            elif value + str(char) not in self.symbols:
                break

            value += char
            self._char_pos += 1

        return value, 'symbol'
