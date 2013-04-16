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

        # Holds allocated size of main memory and num registers
        self._mm_size = 65536
        self._reg_size = 2048

        # Holds stack pointer, frame pointer, register pointer
        self._sp = 0
        self._fp = 0
        self._reg = 0

        # Holds the tabcount of the code. tab_push, tab_pop manipulate this
        self._tab_count = 0

        # Holds an integer used for unique label generation for if/loop
        self._label_id = 0

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
        code = [
            '#include <stdio.h>',
            '#include <string.h>',
            '',
            '#define MM_SIZE ' + str(self._mm_size),
            '#define R_SIZE  ' + str(self._reg_size),
            '',
            'int main(void)',
            '{',
            '// allocate main memory',
            'int MM[MM_SIZE];',
            '',
            '// allocate register space',
            'int R[R_SIZE];',
            '',
            '// allocate float registers',
            'float R_FLOAT_1;',
            'float R_FLOAT_2;',
            '',
            '// allocate stack/frame pointer space in mm',
            'int SP = R_SIZE - 1;',
            'int FP = R_SIZE - 2;',
            '',
            'goto _entry;',
            '',
        ]

        self.generate('\n'.join(code), tabs=0)

        return

    def generate_footer(self):
        """Generate Code Footer
        """
        code = [
            '',
            '_end:',
            '    return 0;',
            '}',
        ]

        self.generate('\n'.join(code), tabs=0)

        return

    def generate(self, code, tabs=-1):
        """Generate Code
        """
        tabs = tabs if tabs != -1 else self._tab_count
        self._generated_code += ('    ' * tabs) + code + '\n'

        return

    def tab_push(self):
        self._tab_count += 1
        return

    def tab_pop(self):
        self._tab_count -= 1 if self._tab_count != 0 else 0
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

    def get_stack_space(self, id_size):
        """Get Memory Space
        """
        # Determine size of the identifier
        mem_needed = int(id_size) if id_size is not None else 1
        
        # Get the next memory space from the stack pointer
        var_loc = self._sp

        # Bump the stack pointer to the next location
        self._sp += mem_needed

        return var_loc

    def get_reg(self, inc=True):
        """Get Register
        """
        # Increment the register if we're getting a brand new one
        self._reg += 1 if inc else 0

        return self._reg

    def get_label_id(self):
        """Get Label Id
        """
        self._label_id += 1

        return self._label_id

    def do_operation(self, reg1, type1, reg2, type2, operation):
        """Do Operation
        """
        # Get a register to hold the operation result
        result = self.get_reg()

        if type1 != 'float' and type2 != 'float':
            self.generate('R[%d] = R[%d] %s R[%d];' %
                    (result, reg1, operation, reg2))
            return result

        if type1 != 'float':
            self.generate('R_FLOAT_1 = R[%d];' % reg1)
        else:
            self.generate('memcpy(&R_FLOAT_1, &R[%d], sizeof(float));' % reg1)

        if type2 != 'float':
            self.generate('R_FLOAT_2 = R[%d];' % reg2)
        else:
            self.generate('memcpy(&R_FLOAT_2, &R[%d], sizeof(float));' % reg2)

        self.generate('R_FLOAT_1 = R_FLOAT_1 %s R_FLOAT_2;' % operation)
        self.generate('memcpy(&R[%d], &R_FLOAT_1, sizeof(float));' % result)
        
        return result
