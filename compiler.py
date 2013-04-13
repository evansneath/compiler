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
from subprocess import call

# Import custom compiler libraries
from lib.parser import Parser


def parse_arguments():
    """Parse Arguments

    Parses all command line arguments for the compiler program.

    Returns:
        An object containing all expected command line arguments.
    """
    # Parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='print debug information',
            action='store_true')
    parser.add_argument('source', help='source file to compile')
    parser.add_argument('-o', '--out', help='target path for the compiled code',
            action='store', default='a.out')
    args = parser.parse_args()

    return args

def compile(source, target, debug=False):
    """Compile

    Executes the compilation process given a source file path.

    Arguments:
        source: The source file to compile.
        target: The destination binary executable file.
        debug: If True, verbose parsing details are shown. (Default: False)

    Returns:
        True on success, False otherwise.
    """
    # Define a temporary location for the intermediate C code
    TMP_CODE_FILE = './ir.c'

    # Create a Parser object to parse the inputted source file
    parser = Parser(debug)

    # Parse the source file to the temporary code file
    if not parser.parse(source, TMP_CODE_FILE):
        print('Error while parsing "'+source+'"')
        return False

    # Set up gcc compilation command
    gcc_cmd = ['gcc', '-m32', '-lm', '-o', target, TMP_CODE_FILE]

    # Compile the temporary file with gcc. Output to the target location
    if call(gcc_cmd) != 0:
        print('Error while compiling "'+target+'"')
        return False

    return True

if __name__ == '__main__':
    # Parse compiler arguments
    args = parse_arguments()

    # Run compilation process
    compile(args.source, args.out, debug=args.debug)

    # Terminate program
    exit()
