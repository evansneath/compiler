Compiler
========

##Description
A compiler for a made-up language.

##Author
Created by [Evan Sneath](http://github.com/evansneath).

##License
This software licensed under the [Open Software License v3.0](http://www.opensource.org/licenses/OSL-3.0).

##Dependencies
In order to run, this software requires the following dependencies:

* [Python 3.3](http://python.org/download/releases/3.3.0/)

##Progress

<table>
<tr><td><b>Component</b></td><td><b>Status</b></td></tr>
<tr><td>Scanning</td><td>Completed</td></tr>
<tr><td>Parsing</td><td>Completed</td></tr>
<tr><td>Type Checking</td><td>Completed</td></tr>
<tr><td>Code Generation</td><td>In Progress</td></tr>
<tr><td>Runtime</td><td>Not Started</td></tr>
</table>

##Usage
```
usage: compiler.py [-h] [-d] [-o OUT] source

positional arguments:
  source             source file to compile

optional arguments:
  -h, --help         show this help message and exit
  -d, --debug        print debug information
  -o OUT, --out OUT  target path for the compiled code
```

At the moment, the compiler will scan the source file for all valid tokens and 
parse the language grammar. All scanner, parser, and type errors will be 
outputted as they are encountered. Generated code is then outputted to `ir.c`
where it is then run through the `gcc` compiler.

The `tests/` directory contains test source files which have several examples 
of token scanning with error/warning handling and grammar parsing.
