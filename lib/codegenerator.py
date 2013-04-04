#!/usr/bin/env python3

"""CodeGenerator module

Provides functionality for code output to a attached destination file.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    CodeGenerator: A code generator interface for destination file outputting.
"""

class CodeGenerator(object):
    """CodeGenerator class

    This class implements code generator function calls to easily attach a
    destination file, input code to generate, and commit the destination
    file upon successful compilation. This class is designed to be subclassed
    the be used during the parsing stage of the compiler.

    Methods:
        attach_destination: Binds a destination file to the code generator.
        generate_header: Generates all overhead code (memory allocation, etc).
        generate: Formats and stores a given string of code for later output.
        commit: Commits all code generation and writesto the destination file.
        rollback: Wipes all generated code up to this point.
    """
    def __init__(self):
        super(CodeGenerator, self).__init__()

        # Holds the file path of the attached destination file
        self._dest_path = ''

        # Holds all generated code to be written to the file destination
        self._generated_code = ''

        return

    def attach_destination(self, dest_path):
        """Attach Destination

        Attaches a destination file to the code generator and prepares the
        file for writing.

        Arguments:
            dest_path: The path to the destination file to write.

        Returns:
            True on success, False otherwise.
        """
        # The target file was attached, store the path
        self._dest_path = dest_path

        return True

    def generate_header(self):
        """Generate Code Header
        """
        self.generate('// This is a test program')

        return

    def generate(self, code):
        """Generate Code
        """
        self._generated_code += code + '\n'

        return

    def commit(self):
        """Commit Code Generation
        """
        try:
            with open(self._dest_path, 'w+') as f:
                f.write(self._generated_code)
        except IOError as e:
            print('Error: "{0}"'.format(dest_path))
            print('    Could not write to destination file: %s' % e.strerror)
            return False

        return True

    def rollback(self):
        """Rollback Code Generation
        """
        self._generated_code = ''

        return


