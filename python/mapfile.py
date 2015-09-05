#!/usr/bin/python

"""Parse files stored in the RFC 822 metaformat."""

from re import compile as Regex

def enumerate_with_offset(iterable, offset):
    """Enumerate the given sequence, but have the index offset by the specified
    amount."""
    for i, item in enumerate(iterable):
        yield i + offset, item

def get_indent(string, total=0):
    """Find the size of the indent of the string."""
    if not string[0].isspace():
        return total
    return get_indent(string[1:], total + 1)

def load(string, required=None, callbacks=None):
    """Parse the given string.  Raises a ParseError if any problems are
    encountered, including if any field in required is not included.  Callbacks
    is a dictionary of functions, listed by field, with the signature (mapping,
    line_number)."""
    if callbacks is None:
        callbacks = {}
    lines = string.splitlines()
    mapping = {}
    #Skip blank lines at the beginning of the file
    offset = 0
    for offset, line in enumerate(lines):
        if line and not line.isspace():
            break
    current_line, lines = lines[offset], lines[offset:]
    current_line_number = offset
    indent_size = get_indent(current_line)
    comment = Regex(r"(?<!\\)#.*$")
    line_numbers = {}
    for line_number, indented_line in enumerate_with_offset(lines, offset + 1):
        indent, line = indented_line[:indent_size], indented_line[indent_size:]
        line = comment.sub("", line)
        if indent and not indent.isspace():
            raise ParseError("Unexpected unindent.", line_number,
                             indented_line)
        if not line or line[0].isspace():
            current_line += line
        else:
            field, value = pairify(current_line, current_line_number)
            mapping[field] = value
            line_numbers[field] = current_line_number
            current_line = line
            current_line_number = line_number
    field, value = pairify(current_line, current_line_number)
    mapping[field] = value
    line_numbers[field] = current_line_number
    if required is not None:
        for field in required:
            if field not in mapping:
                raise ParseError("Required field \"%s\" missing." % field)
    for field in callbacks.iterkeys():
        line_number = line_numbers[field] if field in line_numbers else None
        callbacks[field](mapping, line_number)
    return mapping

def pairify(string, line_number):
    """Convert a string of the form "key: value" to a tuple ("key",
    "value").  May raise a ParseError."""
    if ":" not in string:
        raise ParseError("Keys must be terminated with a colon.", line_number,
                         string)
    items = string.split(":", 1)
    field = items[0].strip()
    value = ":".join(item.strip() for item in items[1:])
    return field, value

class ParseError(Exception):
    def __init__(self, message, line_number=None, line=None):
        super(ParseError, self).__init__(message)
        self.line_number = line_number
        self.line = line

    def __str__(self):
        if self.line_number is not None:
            message = "Line %d: " % self.line_number
        else:
            message = ""
        message += super(ParseError, self).__str__()
        if self.line is not None:
            message += "\n" + self.line
        return message

#******************************************************************************
#********************************* UNIT TESTS *********************************
#******************************************************************************

from py.test import raises

def test_get_indent():
    assert 0 == get_indent("stuff")
    assert 1 == get_indent(" stuff")
    assert 2 == get_indent("  stuff")
    assert 3 == get_indent("   stuff")

def test_load():
    string = "\n".join(["thing: stuff#comment", "#comment", "your: mom",
                        "sucks: xkcd"])
    assert {"thing": "stuff", "your": "mom", "sucks": "xkcd"} == load(string)
