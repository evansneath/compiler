#!/usr/bin/env python3

"""Types module

Provides data structures necessary for identifier tracking and handling in the
compilation process as well as tokenizing.

Author: Evan Sneath
License: Open Software License v3.0

Classes:
    Token: A named tuple object containing token information.
    Identifier: A named tuple object containing identifier information.
    Parameter: A named tuple object containing procedure param information.
    IdentifierTable: Extends the list type to provide ID table functionality.
"""

from lib.errors import ParserNameError
from collections import namedtuple


"""Token class

A named tuple object factory containing token information.

Attributes:
    type: The data type of the token to be stored.
    value: The value of the token being stored.
    line: The line number on which the token was encountered.
"""
Token = namedtuple('Token', ['type', 'value', 'line'])


"""Identifier class

A named tuple object factory containing identifier information.

Attributes:
    name: The identifier name. This acts as the dictionary key.
    type: The data type of the identifier.
    size: The number of elements of the identifier if a variable.
        If procedure, program, or non-array type, None is expected.
    params: A list of Parameter class objects describing procedure params.
    mm_ptr: A pointer to the location of the identifier in main memory.
"""
Identifier = namedtuple('Identifier',
        ['name', 'type', 'size', 'params', 'mm_ptr'])


"""Parameter class

A named tuple object factory containing procedure parameter information.

Attributes:
    id: The Identifier named tuple of the parameter.
    direction: The direction ('in' or 'out') of the parameter.
"""
Parameter = namedtuple('Parameter', ['id', 'direction'])


class IdentifierTable(list):
    """IdentifierTable class

    Extends the List built-in type with all methods necessary for identifier
    table management during compilation.

    Methods:
        push_scope: Adds a new scope.
        pop_scope: Removes the highest scope.
        add: Adds a new identifier to the current or global scope.
        find: Determines if an identifier is in the current of global scope.
        get_id_location: Determines where the identifier exists in the scope.
        is_global: Determines if an identifier exists in the global scope.
        is_param: Determines if an identifier is a parameter of the scope.
        get_param_direction: Gets the direction of the parameter in the scope.
        get_current_scope_owner: Gets the program or procedure name from which
            the current scope was created.
    """
    def __init__(self):
        super().__init__()

        # Create the global scope
        self.append({})

        # Create a list of scope parent names (the owner of the scope)
        self._owner_ids = ['global']

        return

    def push_scope(self, owner_id):
        """Push New Identifier Scope

        Creates a new scope on the identifiers table and increases the global
        current scope counter.

        Arguments:
            owner_id: The name of the identifier which has created this scope.
        """
        # Create a brand new scope for the identifiers table
        self.append({})

        # Save the owner of this scope for future lookup
        self._owner_ids.append(owner_id)

        return

    def pop_scope(self):
        """Pop Highest Identifier Scope

        Disposes of the current scope in the identifiers table and decrements
        the global current scope counter.
        """
        # Remove this entire scope from the identifiers table
        self.pop(-1)

        # Remove the identifier from the owner list
        self._owner_ids.pop()

        return

    def add(self, identifier, is_global=False):
        """Add Identifier to Scope

        Adds a new identifier to either the current scope of global.

        Arguments:
            identifier: An Identifier named tuple object describing the new
                identifier to add to the table.
            is_global: Determines whether the identifier should be added to
                the current scope or the global scope. (Default: False)

        Raises:
            ParserNameError if the identifier has been declared at this scope.
        """
        scope = -1 if not is_global else 0

        if is_global and len(self) > 2:
            raise ParserNameError('global name must be defined in program scope')

        if is_global and (identifier.name in self[0] or (len(self) > 1 and
                          identifier.name in self[1])):
            raise ParserNameError('name already declared at this scope')

        if not is_global and identifier.name in self[-1]:
            raise ParserNameError('name already declared at this scope')

        self[scope][identifier.name] = identifier

        return

    def find(self, name):
        """Find Identifier in Scope

        Searches for the given identifier in the current and global scope.

        Arguments:
            name: The identifier name for which to search.

        Returns:
            An Identifier named tuple containing identifier name, type and size
            information if found in the current or global scopes.

        Raises:
            ParserNameError if the given identifier is not found in any valid scope.
        """
        if name in self[-1]:
            identifier = self[-1][name]
        elif name in self[0]:
            identifier = self[0][name]
        else:
            raise ParserNameError()

        return identifier

    def get_id_location(self, name):
        """Get Identifier Location

        Determines the location of the identifier in the stack based on the
        identifier's place in the id table.

        Arguments:
            name: The identifier name for which to search.

        Returns:
            A string value for the location of the identifier in the stack.
            This may be 'global', 'param', or 'local'.
        """
        if self.is_global(name):
            return 'global'
        elif self.is_param(name):
            return 'param'

        return 'local'

    def is_global(self, name):
        """Identifier is Global

        Determines if an identifier exists in the global scope.

        Arguments:
            name: The identifier name for which to search.

        Returns:
            True if the identifier exists in the global scope. False otherwise.
        """
        return name in self[0]

    def is_param(self, name):
        """Identifier is Parameter

        Determines if an identifier is a parameter in the current scope.

        Arguments:
            name: The identifier name for which to search.

        Returns:
            True if the identifier is a scope parameter. False otherwise.
        """
        owner = self.get_current_scope_owner()

        if owner == 'global' or not owner.params:
            return False

        for param in owner.params:
            if name == param.id.name:
                return True

        return False

    def get_param_direction(self, name):
        """Get Parameter Direction

        If the name given is a valid parameter of the scope, the direction
        ('in' or 'out') will be returned.

        Arguments:
            name: The identifier name for which to search.

        Returns:
            'in' or 'out' depending on the parameter direction. None if the
            name given is not a valid parameter of the current scope.
        """
        owner = self.get_current_scope_owner()
        
        if owner == 'global':
            return None

        for param in owner.params:
            if name == param.id.name:
                return param.direction

        return None

    def get_current_scope_owner(self):
        """Get Current Scope Owner

        Returns the Identifier object of the owner of the current scope. This
        owner will either be a 'program' or 'procedure' type.

        Returns:
            The Identifier object of the owner of the current scope. None if
            the current scope is the global scope.
        """
        owner = self._owner_ids[-1]

        # If this is the global scope, return no owner
        return self[-1][self._owner_ids[-1]] if owner != 'global' else None
