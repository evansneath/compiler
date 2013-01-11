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

    # Create a keyword list for the scanner
    keywords = ['while', 'if', 'then', 'else', 'end', '+', '-', ':=', '==',
                '(', ')', ';', 'true', 'false', '//']

    def __init__(self):
        super(Scanner, self).__init__()

        # Holds all source file data (code) to be scanned
        self.src = None

        # Holds the location of the next character to scan in the source file
        self.line_pos = 0
        self.char_pos = 0

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

    def scan(self):
        """Scan For Next Token

        Scans the source code for the next token. The next token is then
        returned for parsing.

        Returns:
            The next token object in the source code.
        """
        value = ''

        # Find the next line if we hit a newline
        while self.src[self.line_pos][self.char_pos] == '\n':
            self.line_pos += 1
            self.char_pos = 0

            if self.line_pos >= len(self.src):
                return self.Token('eof', None, self.line_pos)

        # Find the next non-space character
        while self.src[self.line_pos][self.char_pos].isspace():
            self.char_pos += 1

        # Get the value
        while True:
            # Get the next character
            char = self.src[self.line_pos][self.char_pos]

            # See if we've hit a space or this character is a keyword
            if char in self.keywords and value == '':
                value = char
                self.char_pos += 1
                break
            elif (char in self.keywords and value != '') or char.isspace():
                break

            # Append the character to the value
            value += char

            # Increment the character position in the line
            self.char_pos += 1

        # Determine what this value is
        type = 'unknown'
        if value in self.keywords:
            type = 'keyword'
        elif value.isdigit():
            type = 'integer'
            value = int(value)
        elif value.isalnum():
            type = 'identifier'

        return self.Token(type, value, self.line_pos)

