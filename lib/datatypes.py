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
    type: The datatype of the token to be stored.
    value: The value of the token being stored.
    line: The line number on which the token was encountered.
"""
Token = namedtuple('Token', ['type', 'value', 'line'])


"""Identifier class

A named tuple object factory containing identifier information.

Attributes:
    name: The identifier name. This acts as the dictionary key.
    type: The datatype of the identifier.
    size: The number of elements of the identifier if a variable.
        If procedure, program, or non-array type, None is expected.
    params: A list of Parameter class objects describing procedure params.
"""
Identifier = namedtuple('Identifier', ['name', 'type', 'size', 'params'])


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
    """
    def __init__(self):
        super(IdentifierTable, self).__init__()

        # Create the global scope
        self.append({})

        return

    def push_scope(self):
        """Push New Identifier Scope

        Creates a new scope on the identifiers table and increases the global
        current scope counter.
        """
        self.append({})

        return

    def pop_scope(self):
        """Pop Highest Identifier Scope

        Disposes of the current scope in the identifiers table and decrements
        the global current scope counter.
        """
        self.pop(-1)

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

        if identifier.name in self[scope]:
            raise ParserNameError()

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
        identifier = None

        if name in self[-1]:
            identifier = self[-1][name]
        elif name in self[0]:
            identifier = self[0][name]
        else:
            raise ParserNameError()

        return identifier


