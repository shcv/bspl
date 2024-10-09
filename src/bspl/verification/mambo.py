"""
Mambo - path queries for verifying arbitrary properties of information protocols

ideas for improvement:
 - precompute event timings from paths, instead of scanning for each parameter
 - share parameter timings between uses within a query
 - split 'or' queries and process separately; should allow more reduction
"""

from math import inf
from .paths import Emission, Reception


def find(path, p):
    """Find the index of the first message in path that contains parameter p"""
    role = None
    if ":" in p:
        role, p = p.split(":")
    for i, e in enumerate(path):
        if role:
            if isinstance(e, Emission) and role != e.sender:
                continue
            if isinstance(e, Reception) and role != e.receiver:
                continue
        if p in e.ins or p in e.outs:
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
        if not val_a:
            return val_b
        if not val_b:
            return val_a
        return min(val_a, val_b)

    return inner


def And(a, b):
    """A clause for path queries that checks if both expressions a and b are satisfied"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        if not val_a:
            return None
        val_b = b(path, **kwargs)
        if not val_b:
            return None
        return max(val_a, val_b)

    return inner


def Not(a):
    """A clause for path queries that checks if expression a is not satisfied"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        if not val_a:
            return inf
        return None

    return inner


def before(a, b):
    """A clause for path queries that checks if a is satisfied before b"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        if not val_a:
            return None
        val_b = b(path, **kwargs)
        if not val_b:
            return None
        if val_a < val_b:
            return val_b

    return inner


class Query:
    def __init__(self, fn, *children):
        if isinstance(children[0], str):
            # leaf node = parameter
            p = children[0]
            self.fn = fn(p)
            if ":" in p:
                role, p = p.split(":")
            self.parameters = set([p])
            self.conflicts = {}
        else:
            # internal node = expression; propagate parameters and conflicts
            self.fn = fn(*children)
            self.parameters = set.union(*[c.parameters for c in children])
            # merge conflict sets from children
            self.conflicts = {}
            for c in children:
                for k, v in c.conflicts.items():
                    if k in self.conflicts:
                        self.conflicts[k].update(v)
                    else:
                        self.conflicts[k] = v

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
        for lp in ast.left.parameters:
            if lp in q.conflicts:
                q.conflicts[lp].update(ast.right.parameters)
            else:
                q.conflicts[lp] = set(ast.right.parameters)
        return q

    def Not(self, ast):
        return Query(Not, ast.right)

    def _default(self, ast):
        return ast
