#!/usr/bin/env python3

"""CodeGenerator module

Provides functionality for code output to a attached destination file.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    CodeGenerator: A code generator interface for destination file outputting.
"""


class CodeGenerator:
    """CodeGenerator class

    This class implements code generator function calls to easily attach a
    destination file, input code to generate, and commit the destination
    file upon successful compilation. This class is designed to be inherited
    the be used during the parsing stage of the compiler.

    Attributes:
        runtime_functions: Details of each runtime function and its params.

    Methods:
        attach_destination: Binds a destination file to the code generator.
        generate_header: Generates overhead code (memory allocation, etc).
        generate_footer: Generates finishing overhead code.
        generate: Formats and stores a given string of code for later output.
        comment: Adds a comment to the generated code with appropriate tabbing.
        tab_push: Increases the tab depth by 1 tab (4 spaces).
        tab_pop: Decreases the tab depth by 1 tab (4 spaces).
        commit: Commits all code generation and writes to the destination file.
        get_mm: Provides a free memory space for global or local variables.
        reset_local_ptr: Resets the value for the local pointer to default.
        reset_param_ptr: Resets the value for the param pointer to default.
        get_reg: Provides a free register for intermediate variable use.
        get_label_id: Returns a unique identifier for the procedure call.
        get_unique_call_id: Returns a unique identifier for multiple calls.
        generate_program_entry: Generates all code associated with setting up
            the program entry and exit point.
        generate_procedure_call: Generates all code associated with managing
            the memory stack during a procedure call.
        generate_procedure_call_end: Generates code to clean up a procedure
            call. This finalizes the call by popping the SP to local stack.
        generate_name: Generates all code associated with name reference.
        generate_assignment: Generates all code associated with id assignment.
        generate_param_push: Generates code to push a param onto the stack.
        generate_param_pop: Generates code to pop a param off the stack.
        generate_param_store: Generates code to save an outgoing parameter
            to an identifier located in main memory.
        generate_number: Generates the code for a number reference.
        generate_return: Generates the code for the 'return' operation.
        generate_operation: Generates operation code given an operation.
    """
    def __init__(self):
        super().__init__()

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

        # Holds the tab count of the code. tab_push, tab_pop manipulate this
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
            '// Define register locations of stack/frame ptr',
            '#define SP       %d' % self._SP,
            '#define FP       %d' % self._FP,
            '#define HP       %d' % self._HP,
            '',
            'int main(void)',
            '{',
            '// Allocate main memory and register space',
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
            '// Allocate float registers',
            'float R_FLOAT_1;',
            'float R_FLOAT_2;',
            '',
            '// Allocate space for a string buffer',
            'char STR_BUF[BUF_SIZE];',
            '',
            '////////////////////////////////////////////////////',
            '// PROGRAM START',
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
            '////////////////////////////////////////////////////',
            '// RUNTIME FUNCTIONS',
            '',
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

        Pushes the tab (increases the indentation by 4 spaces) for pretty
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
            print('Error: "%s"' % self._dest_path)
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
        the stack. This is used to properly allocate space for the local
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
        self._param_ptr = 1
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

    def generate_program_entry(self, program_name, program_num, debug):
        """Generate Program Entry

        Generates the code associated with managing the entry point for the
        program. This involves pushing the program return address onto the
        stack, jumping to the entry point, and creating the program exit
        section.

        Arguments:
            program_name: The name of the program.
            program_num: The label id of the program.
            debug: Determines if comments should be written to the code.
        """
        # Push the return address onto the stack
        self.comment('Setting program return address', debug)
        self.generate('MM[R[FP]] = (int)&&%s_%d_end;' %
                      (program_name, program_num))

        # Make the jump to the entry point
        self.generate('goto %s_%d_begin;' % (program_name, program_num))

        # Make the main program return
        self.generate('')
        self.comment('Creating the program exit point', debug)
        self.generate('%s_%d_end:' % (program_name, program_num))
        self.tab_push()
        self.generate('return 0;')
        self.tab_pop()
        self.generate('')

        return

    def generate_procedure_call(self, procedure_name, procedure_num, debug):
        """Generate Procedure Call

        Generates the code associated with managing the stack before and
        after a procedure call. Note that this does not include param
        pushing and popping operations.

        Arguments:
            procedure_name: The name of the procedure to call.
            procedure_num: The label id of the procedure to call.
            debug: Determines if comments should be written to the code.
        """
        # Save the FP to the stack. Set next FP to return address
        self.comment('Setting caller FP', debug)
        self.generate('R[SP] = R[SP] - 1;')
        self.generate('MM[R[SP]] = R[FP];')
        self.comment('Setting return address (current FP)', debug)
        self.generate('R[SP] = R[SP] - 1;')
        self.generate('R[FP] = R[SP];')

        # Generate a new call number so multiple calls do not cause collisions
        call_number = self.get_unique_call_id()

        # Push the return address onto the stack
        self.generate('MM[R[SP]] = (int)&&%s_%d_%d;' %
                (procedure_name, procedure_num, call_number))
                
        # Make the jump to the function call
        self.generate('goto %s_%d;' % (procedure_name, procedure_num))

        # Generate the return label
        self.generate('%s_%d_%d:' % (procedure_name, procedure_num, call_number))

        # The SP now points to the return address. Restore the old FP
        self.comment('Restore caller FP', debug)
        self.generate('R[SP] = R[SP] + 1;')
        self.generate('R[FP] = MM[R[SP]];')

        return

    def generate_procedure_call_end(self, debug):
        """Generate Procedure Call End

        Generates code to leave the procedure on the stack by pushing the
        stack to the lower scope's local stack.

        Arguments:
            debug: Determines if comments are to be written in generated code.
        """
        self.comment('Move to caller local stack', debug)

        # Finalize the function call. Move the SP off the param list
        self.generate('R[SP] = R[SP] + 1;')

        return

    def _generate_get_id_in_mm(self, id_obj, id_location, idx_reg, debug):
        """Generate Get Identifier in Main Memory (Protected)

        Knowing the location in the stack and the offset (mm_ptr) value of
        a given index, code is generated to calculate the exact location of
        the identifier in main memory.

        If identifier is param, offset is the parameter offset.
        If identifier is local, offset is the local offset.
        If identifier is global, offset is the local offset of program scope.

        Arguments:
            id_obj: The Identifier class object containing id data.
            id_location: Either 'global', 'param', or 'local' depending on the
                location in the stack where the identifier resides.
            idx_reg: The register number of the index expression.
            debug: Determines if comments are to be written in generated code.

        Returns:
            The register number of the calculated address of the identifier.
        """
        # Get a new register to calculate the main memory address of this id
        id_reg = self.get_reg()

        self.generate('R[%d] = %d;' % (id_reg, id_obj.mm_ptr))

        if id_obj.size is not None and idx_reg is not None:
            self.generate('R[%d] = R[%d] + R[%d];' %
                    (id_reg, id_reg, idx_reg))

        if id_location == 'param':
            self.comment('Param referenced', debug)
            self.generate('R[%d] = R[FP] + 1 + R[%d];' % (id_reg, id_reg))
        elif id_location == 'global':
            self.comment('Global var referenced', debug)
            self.generate('R[%d] = MM_SIZE - 1 - R[%d];' % (id_reg, id_reg))
        else:
            self.comment('Local var referenced', debug)
            self.generate('R[%d] = R[FP] - R[%d];' % (id_reg, id_reg))

        return id_reg

    def generate_name(self, id_obj, id_location, idx_reg, debug):
        """Generate Name

        Generates all code necessary to place the contents of the memory
        location of a given identifier into a new register for computation.

        Arguments:
            id_obj: The Identifier class object containing id data.
            id_location: Either 'global', 'param', or 'local' depending on the
                location in the stack where the identifier resides.
            idx_reg: The register number of the index expression.
            debug: Determines if comments are to be written in generated code.
        """
        # Calculate the position of the identifier in main memory
        id_reg = self._generate_get_id_in_mm(id_obj, id_location, idx_reg,
                                             debug)

        # Retrieve the main memory location and place it in the last register
        self.generate('R[%d] = MM[R[%d]];' % (id_reg, id_reg))

        return

    def generate_assignment(self, id_obj, id_location, idx_reg, expr_reg,
                            debug):
        """Generate Assignment

        Generates all code necessary to place the outcome of an expression
        into the proper location of the identifier in main memory.

        Arguments:
            id_obj: The Identifier class object containing id data.
            id_location: Either 'global', 'param', or 'local' depending on the
                location in the stack where the identifier resides.
            idx_reg: The register number of the index expression.
            expr_reg: The register number of the expression outcome.
            debug: Determines if comments are to be written in generated code.
        """
        # Calculate the position of the identifier in main memory
        id_reg = self._generate_get_id_in_mm(id_obj, id_location, idx_reg,
                                             debug)

        # Set the main memory value to the value in the expression register
        self.generate('MM[R[%d]] = R[%d];' % (id_reg, expr_reg))

        return

    def generate_param_push(self, expr_reg, debug):
        """Generate Param Push

        Generates code to push a parameter onto the procedure stack given
        a register containing the expression outcome.

        Arguments:
            expr_reg: The register number of the expression outcome.
            debug: Determines if comments are to be written in generated code.
        """
        self.comment('Pushing argument onto the stack', debug)
        self.generate('R[SP] = R[SP] - 1;')
        self.generate('MM[R[SP]] = R[%d];' % expr_reg)

        return

    def generate_param_pop(self, param_name, debug):
        """Generate Param Pop

        Pops a parameter off of the stack (moves the SP) and prints a
        comment stating which parameter this is.

        Arguments:
            param_name: The parameter name to display.
            debug: Determines if comments are to be written in generated code.
        """
        self.comment('Popping "%s" param off the stack' % param_name, debug)
                
        # Move to the next memory space
        self.generate('R[SP] = R[SP] + 1;')

        return

    def generate_param_store(self, id_obj, id_location, debug):
        """Generate Param Store

        Calculates the memory location of the destination and placed the
        value of the popped parameter (at current SP) in that location.

        Arguments:
            id_obj: The Identifier class object containing id data.
            id_location: Either 'global', 'param', or 'local' depending on the
                location in the stack where the identifier resides.
            debug: Determines if comments are to be written in generated code.
        """
        # Calculate the position of the parameter output location in main mem
        id_reg = self._generate_get_id_in_mm(id_obj, id_location, None, debug)

        # Store the parameter in the position pointed to by the SP
        self.generate('MM[R[%d]] = MM[R[SP]];' % id_reg)

        return

    def generate_number(self, number, token_type, negate):
        """Generate Number

        Generates the code to store a parsed number in a new register.

        Arguments:
            number: The parsed number value (this is a string representation).
            token_type: The type of the number (either 'integer' or 'float')
            negate: A boolean to determine whether or not to negate the value.
        """
        reg = self.get_reg()

        if token_type == 'integer':
            # This is an integer value, set it to the register
            if negate:
                self.generate('R[%d] = -%s;' % (reg, number))
            else:
                self.generate('R[%d] = %s;' % (reg, number))
        else:
            # This is a float value, place it in the float buffer and copy it
            # to the register
            if negate:
                self.generate('R_FLOAT_1 = -%s;' % number)
            else:
                self.generate('R_FLOAT_1 = %s;' % number)

            self.generate('memcpy(&R[%d], &R_FLOAT_1, sizeof(float));' % reg)

        return

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

        # Go to the return label to exit the procedure
        self.comment('Return to calling function', debug)
        self.generate('goto *(void*)MM[R[FP]];')

        return

    def generate_operation(self, reg1, type1, reg2, type2, operation):
        """Generate Operation

        Given an operation and operand registers with their types, code is
        generated to perform these operations.

        Arguments:
            reg1: The register of the first operand.
            type1: The type of the first operand.
            reg2: The register of the second operand.
            type2: The type of the second operand.
            operation: The operation symbol to perform.

        Returns:
            The register number where the result of the operation
            is stored.
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
