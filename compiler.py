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
    parser.add_argument('source', nargs='+', help='source code to compile')
    args = parser.parse_args()

    # Create a scanner object to parse the inputted source file
    parser = Parser()

    for file in args.source:
        parser.parse(file)

    return


if __name__ == '__main__':
    main()

