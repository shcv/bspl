#!/usr/bin/env python3
import re


def identity(x):
    return x


def merge(*dicts):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


def abort(message):
    """Exit the script with an error message"""
    print(message)
    raise SystemExit(1)


def camel_to_snake(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def cap_first(s):
    if len(s) == 0:
        return s
    else:
        return s[0].capitalize() + s[1:]
