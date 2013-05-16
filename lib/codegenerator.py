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
        generate_header: Generates start overhead code (memory allocation, etc).
        generate_footer: Generates finishing overhead code.
        generate: Formats and stores a given string of code for later output.
        comment: Adds a comment to the generated code with appropriate tabbing.
        tab_push: Increases the tab depth by 1 tab (4 spaces).
        tab_pop: Decreases the tab depth by 1 tab (4 spaces).
        commit: Commits all code generation and writesto the destination file.
        rollback: Wipes all generated code up to this point.
        get_mm: Provides a free memory space for global or local variables.
        get_reg: Provides a free register for intermediate variable use.
        get_label_id: Returns a unique identifier for the procedure call.
        get_unique_call_id: Returns a unique identifier for multiple calls.
        do_operation: Generates operation code given an operation.
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

        # Holds stack pointer register, frame pointer register
        self._SP = 0
        self._FP = 1

        # Holds the pointer to the lowest unused register for allocation
        self._reg = 2

        # Holds the heap pointer to store the current available loc in heap
        self._heap_ptr = 0

        # Holds the local memory pointer which determines the offset from the
        # frame pointer in the current scope. This offset starts at 1.
        self._local_ptr = 1

        # Holds the param memory pointer which determines the offset from the
        # frame pointer in the current scope. This offset starts at 1.
        self._param_ptr = 1

        # Holds the tabcount of the code. tab_push, tab_pop manipulate this
        self._tab_count = 0

        # Holds an integer used for unique label generation for if/loop
        self._label_id = 0

        # Holds an integer to distinguish multiple calls of a function
        self._unique_id = 0

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
            '#define MM_SIZE %d' % self._mm_size,
            '#define R_SIZE  %d' % self._reg_size,
            '',
            '// define register locations of stack/frame ptr',
            '#define SP      %d' % self._SP,
            '#define FP      %d' % self._FP,
            '',
            'int main(void)',
            '{',
            '// allocate main memory and register space',
            'int MM[MM_SIZE];',
            'int R[R_SIZE];',
            '',
            'R[SP] = MM_SIZE - 1;',
            'R[FP] = MM_SIZE - 1;',
            '',
            '// allocate float registers',
            'float R_FLOAT_1;',
            'float R_FLOAT_2;',
            '',
        ]

        self.generate('\n'.join(code), tabs=0)

        return

    def generate_footer(self):
        """Generate Code Footer
        """
        code = [
            '',
            '    // Jump to the program exit',
            '    goto *(void*)MM[R[FP]];',
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

    def comment(self, text, is_displayed=False):
        if is_displayed:
            self.generate('// %s' % text)

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

    def get_mm(self, id_size, is_global=False, is_param=False):
        """Get Memory Space
        """
        var_loc = 0

        # Determine size of the identifier
        mem_needed = int(id_size) if id_size is not None else 1
        
        if is_global:
            # Allocate memory in the global heap space
            var_loc = self._heap_ptr
            self._heap_ptr += mem_needed
        elif is_param:
            var_loc = self._param_ptr
            self._param_ptr += mem_needed
        else:
            # Allocate memory in the local variable space
            var_loc = self._local_ptr
            self._local_ptr += mem_needed

        return var_loc

    def reset_local_ptr(self):
        """Reset Local Pointer
        """
        self._local_ptr = 1
        return

    def reset_param_ptr(self):
        """Reset Param Pointer
        """
        self._param_ptr = 2
        return

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

    def get_unique_call_id(self):
        """Get Unique Call Id
        """
        self._unique_id += 1

        return self._unique_id

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
