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

    Oversees the execution of each stage of the compiler.

    Returns:
        True on success, False otherwise.
    """
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='Compile source code')
    parser.add_argument('source',
                        nargs=1,
                        help='the source code to compile') 
    parser.add_argument('target',
                        nargs=1,
                        help='the target location of the compiled source code')
    args = parser.parse_args()

    # Create a scanner object to parse the inputted source file
    scanner = Scanner()

    if not scanner.attach_file(args.source[0]):
        print('Compilation failed')
        return False

    while True:
        token = scanner.next_token()

        if token.type == 'eof':
            break

        print(token)

    return True


if __name__ == '__main__':
    main()

