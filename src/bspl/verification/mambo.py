#!/usr/bin/env python3

from math import inf
from .paths import Emission, Reception


def find(path, p):
    """Find the index of the first message in path that contains parameter p"""
    for i, e in enumerate(path):
        if ":" in p:
            role, p = p.split(":")
            if isinstance(e, Emission) and role != e.sender:
                continue
            if isinstance(e, Reception) and role != e.receiver:
                continue
        if p in e.ins.union(e.outs):
            # nils don't count
            return i


def occurs(p):
    """A clause for path queries that checks if a parameter occurs"""

    def inner(path=None, **kwargs):
        return find(path, p)

    return inner


def Or(a, b):
    """A clause for path queries that checks if either expression a or b is satisfied"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        val_b = b(path, **kwargs)
        if val_a == None:
            return val_b
        if val_b == None:
            return val_a
        return min(val_a, val_b)

    return inner


def And(a, b):
    """A clause for path queries that checks if both expressions a and b are satisfied"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        if val_a == None:
            return None
        val_b = b(path, **kwargs)
        if val_b == None:
            return None
        return max(val_a, val_b)

    return inner


def Not(a):
    """A clause for path queries that checks if expression a is not satisfied"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        if val_a == None:
            return inf
        return None

    return inner


def before(a, b):
    """A clause for path queries that checks if a is satisfied before b"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        if val_a == None:
            return None
        val_b = b(path, **kwargs)
        if val_b == None:
            return None
        return val_a < val_b

    return inner


class Query:
    def __init__(self, fn, *children):
        if isinstance(children[0], str):
            # leaf node = parameter
            self.fn = fn(children[0])
            self.parameters = set(children)
            self.conflicts = set()
        else:
            # internal node = expression; propagate parameters and conflicts
            self.fn = fn(*children)
            self.parameters = set.union(*[c.parameters for c in children])
            self.conflicts = set.union(*[c.conflicts for c in children])

    def __call__(self, path=None, **kwargs):
        return self.fn(path, **kwargs)


class QuerySemantics:
    def parameter(self, ast):
        return Query(occurs, ast)

    def And(self, ast):
        return Query(And, ast.left, ast.right)

    def Or(self, ast):
        return Query(Or, ast.left, ast.right)

    def Before(self, ast):
        q = Query(before, ast.left, ast.right)
        q.conflicts.update(
            set((lp, rp) for lp in ast.left.parameters for rp in ast.right.parameters)
        )
        return q

    def Not(self, ast):
        return Query(Not, ast.right)

    def _default(self, ast):
        return ast
