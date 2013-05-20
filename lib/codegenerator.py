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
        get_mm: Provides a free memory space for global or local variables.
        get_reg: Provides a free register for intermediate variable use.
        get_label_id: Returns a unique identifier for the procedure call.
        get_unique_call_id: Returns a unique identifier for multiple calls.
        generate_return: Generates the code for the 'return' operation.
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
        self._buf_size = 256

        # Holds stack pointer, frame pointer, and heap pointer registers
        self._SP = 1
        self._FP = 2
        self._HP = 3

        # Holds the pointer to the lowest unused register for allocation
        self._reg = 4

        # Holds the local memory pointer which determines the offset from the
        # frame pointer in the current scope.
        self._local_ptr = 0
        self.reset_local_ptr()

        # Holds the param memory pointer which determines the offset from the
        # frame pointer in the current scope.
        self._param_ptr = 0
        self.reset_param_ptr()

        # Holds the tabcount of the code. tab_push, tab_pop manipulate this
        self._tab_count = 0

        # Holds an integer used for unique label generation for if/loop
        self._label_id = 0

        # Holds an integer to distinguish multiple calls of a function
        self._unique_id = 0

        # Holds the details of the runtime functions
        self.runtime_functions = {
            'getString': [('my_string', 'string', 'out')],
            'putString': [('my_string', 'string', 'in')],
            'getBool': [('my_bool', 'bool', 'out')],
            'putBool': [('my_bool', 'bool', 'in')],
            'getInteger': [('my_integer', 'integer', 'out')],
            'putInteger': [('my_integer', 'integer', 'in')],
            'getFloat': [('my_float', 'float', 'out')],
            'putFloat': [('my_float', 'float', 'in')],
        }

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

        Adds all header code to the generated code buffer.
        """
        code = [
            '#include <stdio.h>',
            '#include <string.h>',
            '',
            '#define MM_SIZE  %d' % self._mm_size,
            '#define R_SIZE   %d' % self._reg_size,
            '#define BUF_SIZE %d' % self._buf_size,
            '',
            '// define register locations of stack/frame ptr',
            '#define SP       %d' % self._SP,
            '#define FP       %d' % self._FP,
            '#define HP       %d' % self._HP,
            '',
            'int main(void)',
            '{',
            '// allocate main memory and register space',
            'int MM[MM_SIZE];',
            'int R[R_SIZE];',
            '',
            '// SP and FP start at the top of MM',
            'R[SP] = MM_SIZE - 1;',
            'R[FP] = MM_SIZE - 1;',
            '',
            '// HP starts at the bottom of MM',
            'R[HP] = 0;',
            '',
            '// allocate float registers',
            'float R_FLOAT_1;',
            'float R_FLOAT_2;',
            '',
            '// allocate space for a string buffer',
            'char STR_BUF[BUF_SIZE];'
            '',
        ]

        self.generate('\n'.join(code), tabs=0)

        return

    def generate_footer(self):
        """Generate Code Footer

        Adds all footer code to the generated code buffer.
        """
        code = [
            '',
            '    // Jump to the program exit',
            '    goto *(void*)MM[R[FP]];',
            '',
            '// Runtime functions are defined here',
            'putString_1:',
            '    R[0] = MM[R[FP]+2];',
            '    printf("%s\\n", (char*)R[0]);',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '',
            'getString_1:',
            '    fgets(STR_BUF, BUF_SIZE, stdin);',
            '    R[0] = strlen(STR_BUF) + 1;',
            '    memcpy(&MM[R[HP]], &STR_BUF, R[0]);',
            '    MM[R[FP]+2] = (int)((char*)&MM[R[HP]]);',
            '    R[HP] = R[HP] + R[0];',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '',
            'putBool_1:',
            '    R[0] = MM[R[FP]+2];',
            '    printf("%s\\n", R[0] ? "true" : "false");',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '',
            'getBool_1:',
            '    scanf("%d", &R[0]);',
            '    R[0] = R[0] ? 1 : 0;',
            '    MM[R[FP]+2] = R[0];',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '',
            'putInteger_1:',
            '    R[0] = MM[R[FP]+2];',
            '    printf("%d\\n", R[0]);',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '',
            'getInteger_1:',
            '    scanf("%d", &R[0]);',
            '    MM[R[FP]+2] = R[0];',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '',
            'putFloat_1:',
            '    R[0] = MM[R[FP]+2];',
            '    memcpy(&R_FLOAT_1, &R[0], sizeof(float));',
            '    printf("%g\\n", R_FLOAT_1);',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '',
            'getFloat_1:',
            '    scanf("%f", &R_FLOAT_1);',
            '    memcpy(&R[0], &R_FLOAT_1, sizeof(float));',
            '    MM[R[FP]+2] = R[0];',
            '    R[0] = MM[R[FP]];',
            '    goto *(void*)R[0];',
            '}',
        ]

        self.generate('\n'.join(code), tabs=0)

        return

    def generate(self, code, tabs=-1):
        """Generate Code
        
        Adds the given code to the generated code and automatically formats
        it with the appropriate tabs and ending newline.

        Arguments:
            code: The code to add to the generated code buffer.
            tabs: A manual override to determine the number of tabs to place
                in this line of code. If -1, then the number of tabs used will
                correspond to the tab location from tab_push() and tab_pop()
                methods. (Default: -1)
        """
        tabs = tabs if tabs != -1 else self._tab_count
        self._generated_code += ('    ' * tabs) + code + '\n'

        return

    def comment(self, text, is_displayed=False):
        """Generate Comment

        Adds a comment to the generated code.

        Arguments:
            text: The text to display in the comment.
            is_displayed: If True, the comment is written to the generated
                code. (Default: False)
        """
        if is_displayed:
            self.generate('// %s' % text)

        return

    def tab_push(self):
        """Tab Push

        Pushes the tab (increases the indentiation by 4 spaces) for pretty
        code output.
        """
        self._tab_count += 1
        return

    def tab_pop(self):
        """Tab Pop

        Pops the tab (decreases the indentation by 4 spaces) for pretty code
        output.
        """
        self._tab_count -= 1 if self._tab_count != 0 else 0
        return

    def commit(self):
        """Commit Code Generation

        Writes the generated code to the destination output file for
        intermediate code if the source is parsed without fatal errors.

        Returns:
            True if file is successfully written, False otherwise.
        """
        try:
            with open(self._dest_path, 'w+') as f:
                f.write(self._generated_code)
        except IOError as e:
            print('Error: "{0}"'.format(dest_path))
            print('    Could not write to destination file: %s' % e.strerror)
            return False

        return True

    def get_mm(self, id_size, is_param=False):
        """Get Memory Space

        Gets a space in memory appropriately depending on if the variable is
        a local variable or a parameter to the scope.

        Arguments:
            id_size: The size of the parameter to allocate (used for arrays).
            is_param: True if the identifier is a parameter, False if local or
                global variable. (Default: False)

        Returns:
            An integer denoting the offset corresponding to a stack landmark
            depending on the type of variable. For example, local variables
            and params are offset by the current FP in different directions
            while global variables are offset by the top of main memory.
            See the documentation in README for stack details.
        """
        var_loc = 0

        # Determine size of the identifier
        mem_needed = int(id_size) if id_size is not None else 1
        
        if is_param:
            var_loc = self._param_ptr
            self._param_ptr += mem_needed
        else:
            # Allocate memory in the local variable space
            var_loc = self._local_ptr
            self._local_ptr += mem_needed

        return var_loc

    def reset_local_ptr(self):
        """Reset Local Pointer

        Resets the pointer to the current scope's local variable portion of
        the stack. This is used to peroperly allocate space for the local
        variables at the start of the scope.
        """
        self._local_ptr = 1
        return

    def reset_param_ptr(self):
        """Reset Param Pointer

        Resets the pointer to the current scope's parameter portion of the
        stack. This is necessary to properly allocate space for the parameters
        as they are being pushed onto the stack.
        """
        self._param_ptr = 2
        return

    def get_reg(self, inc=True):
        """Get Register

        Gets new, unused register from the register list.

        Arguments:
            inc: If True, a new register will be returned. If False, the last
                register allocated will be returned.

        Returns:
            An integer denoting the register number. The register may then be
            referenced as follows: R[<reg_num>]
        """
        # Increment the register if we're getting a brand new one
        self._reg += 1 if inc else 0

        return self._reg

    def get_label_id(self):
        """Get Label Id

        Gets a label id so that no conflicts occur between procedures with
        the same name in difference scopes.

        Returns:
            A label id to append to the procedure label.
        """
        self._label_id += 1

        return self._label_id

    def get_unique_call_id(self):
        """Get Unique Call Id

        Gets a unique call id so that no conflicts occur between return
        labels for procedures with multiple calls.

        Returns:
            A unique id to append to the procedure return label.
        """
        self._unique_id += 1

        return self._unique_id

    def generate_return(self, debug):
        """Generate Return Statement

        Generates code for all operations needed to move to the scope return
        address and execute the jump to the caller scope.

        Arguments:
            debug: Determines if comments should be displayed or not.
        """
        # Smash the local stack
        self.comment('Moving SP to FP (return address)', debug)
        self.generate('R[SP] = R[FP];')

        # Goto the return label to exit the procedure
        self.comment('Return to calling functon', debug)
        self.generate('goto *(void*)MM[R[FP]];')

        return

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
