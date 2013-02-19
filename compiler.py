#!/usr/bin/env python3

"""Compiler module

Acts as the command line interface to the compiler components. When given a
source file, the compilation process will be executed.

Author: Evan Sneath
License: Open Software License v3.0

Functions:
    main: The main call to begin input file compilation given valid arguments.
"""

# Import standard libraries
import argparse

# Import custom compiler libraries
from parser import Parser


def main():
    """Main function

    Oversees the execution of each component of the compiler.
    """
    # Parse the command line arguments
    parser = argparse.ArgumentParser()
    #parser.add_argument('target', help='target path for the compiled code')
    parser.add_argument('source', help='source code to compile')
    args = parser.parse_args()

    # Create a Parser object to parse the inputted source file
    parser = Parser(debug=False)

    if parser.parse(args.source):
        print('Parsed "'+args.source+'"')
    else:
        print('Error while parsing "'+args.source+'"')

    return


if __name__ == '__main__':
    main()
