#!/usr/bin/env python3


class ParserError(Exception):
    """ParserError class

    The base error class for all other parsing errors. This should be caught
    at resync points.
    """
    pass


class ParserSyntaxError(ParserError):
    """ParserSyntaxError class

    Thrown when a syntax error occurs in the parser.
    """
    pass


class ParserNameError(ParserError):
    """ParserNameError class

    Thrown when a name error occurs in the parser.
    """
    pass


class ParserTypeError(ParserError):
    """ParserTypeError class

    Thrown when a type error occurs in the parser.
    """
    pass


class ParserRuntimeError(ParserError):
    """ParserRuntimeError class

    Thrown when a runtime error occurs in the parser.
    """
    pass
