#!/usr/bin/env python3

"""
File:       compiler.py
Author:     Evan Sneath
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
        print('Successfully parsed', args.source)
    else:
        print('Error while parsing', args.source)

    return


if __name__ == '__main__':
    main()

