#!/usr/bin/env python3

"""
File:       compiler.py
Author:     Evan Sneath
"""

# Import standard libraries
import argparse

# Import custom compiler libraries
from scanner import Scanner


def main():
    """Main function

    Oversees the execution of each component of the compiler.
    """
    # Parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('source',
        help='the source code to compile') 
    parser.add_argument('target',
        help='the target location of the compiled source code')
    args = parser.parse_args()

    # Create a scanner object to parse the inputted source file
    scanner = Scanner()

    if not scanner.attach_file(args.source):
        return

    # Print every token until we hit the end of file or an error
    while True:
        token = scanner.next_token()
        print(token)

        if token.type in ['eof', 'error']:
            break

    return


if __name__ == '__main__':
    main()

