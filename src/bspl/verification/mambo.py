"""
Mambo - path queries for verifying arbitrary properties of information protocols

ideas for improvement:
 - precompute event timings from paths, instead of scanning for each parameter
 - share parameter timings between uses within a query
 - split 'or' queries and process separately; should allow more reduction
"""

from math import inf
from dataclasses import dataclass
from typing import Dict, Set, Tuple, Optional, Any, Callable
from .paths import Emission, Reception, empty_path, possibilities, partition


def find(path, p):
    """Find the index of the first message in path that contains parameter p"""
    role = None
    if ":" in p:
        role, p = p.split(":")
    for i, e in enumerate(path):
        if role:
            if isinstance(e, Emission) and role != e.sender:
                continue
            if isinstance(e, Reception) and role != e.recipient:
                continue
        if p in e.ins or p in e.outs:
            # nils don't count
            return i


def check_last(path, p):
    """Check if a parameter is present in the most recent event"""
    role = None
    if ":" in p:
        role, p = p.split(":")
    # only need to look at most recent event
    i = len(path.events) - 1
    if i < 0:
        return
    e = path.events[i]
    if role:
        if isinstance(e, Emission) and role != e.sender:
            return
        if isinstance(e, Reception) and role != e.recipient:
            return
    if p in e.ins or p in e.outs:
        # nils don't count
        return i


@dataclass
class Path:
    """A path that remembers query results"""

    events: Tuple[Any, ...]  # The actual path events
    query_results: Dict[Callable, Optional[int]]  # Memoized results for this path

    @classmethod
    def create_empty(cls) -> "Path":
        """Create an empty path with no events"""
        return Path(empty_path(), {})

    def extend(self, event) -> "Path":
        """Create a new path by adding an event"""
        new_events = self.events + (event,)
        return Path(new_events, self.query_results.copy())

    def __len__(self):
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    def __hash__(self):
        # return hash((self.events, self.parameter_state))
        return hash(self.events)


def occurs(p: str) -> Callable:
    """A clause for path queries that checks if a parameter occurs, returning its first occurrence index as a timestamp"""

    def inner(path: Path, **kwargs) -> Optional[int]:
        return find(path, p)
        # return check_last(path, p)

    inner.__name__ = p
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

    inner.__name__ = "or"
    return inner


def And(a, b):
    """A clause for path queries that checks if both expressions a and b are satisfied"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        val_b = b(path, **kwargs)
        if not isinstance(val_a, int):
            return val_a
        if not isinstance(val_b, int):
            return val_b
        return max(val_a, val_b)

    inner.__name__ = "and"
    return inner


def Not(a):
    """A clause for path queries that checks if expression a is not satisfied"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)

        # leave None cases unresolved
        if val_a == None:
            return None
        if val_a == False:
            return inf
        return False

    inner.__name__ = "not"
    return inner


def before(a, b):
    """A clause for path queries that checks if a is satisfied before b"""

    def inner(path=None, **kwargs):
        val_a = a(path, **kwargs)
        val_b = b(path, **kwargs)
        if not isinstance(val_a, int):
            return val_a
        if not isinstance(val_b, int):
            return val_b

        if val_a < val_b:
            return val_b
        else:
            return False

    inner.__name__ = "before"
    return inner


class Query:
    """A query that remembers its results for each path"""

    def __init__(self, fn, *children):
        self.children = children
        self.fn_type = fn
        if isinstance(children[0], str):
            # Leaf node = parameter
            p = children[0]
            self.fn = fn(p)
            if ":" in p:
                role, p = p.split(":")
            self.parameters = set([p])
            self.conflicts = {}
        else:
            # Internal node = expression; propagate parameters and conflicts
            self.fn = fn(*children)
            self.parameters = set.union(*[c.parameters for c in children])
            self.conflicts = {}
            for c in children:
                for k, v in c.conflicts.items():
                    if k in self.conflicts:
                        self.conflicts[k].update(v)
                    else:
                        self.conflicts[k] = v

    def __call__(self, path: Path, **kwargs) -> Optional[int]:
        # Check if we have a memoized result
        if self in path.query_results:
            return path.query_results[self]

        # Calculate and store the result
        result = self.fn(path, **kwargs)
        if result != None:
            path.query_results[self] = result
        return result

    def __repr__(self):
        return str(self)

    def __str__(self):
        if self.fn_type == occurs:
            return str(self.fn.__name__)
        return f"{self.fn.__name__}({', '.join(str(c) for c in self.children)})"


class QuerySemantics:
    def __init__(self):
        self.parameters = {}

    def parameter(self, ast):
        p = ast
        if p not in self.parameters:
            self.parameters[p] = Query(occurs, ast)
        return self.parameters[p]

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


def extensions(U, path: Path, **kwargs):
    """Generate path extensions"""
    default_kwargs = {
        "by_degree": False,
        "reduction": True,
        "safe": False,
        "debug": False,
    }
    kwargs = {**default_kwargs, **kwargs}

    def sort(p):
        return p.name if not kwargs["by_degree"] else len(U.tangle.incompatible[p])

    ps = possibilities(U, path.events)

    if kwargs["safe"]:
        safe_events = U.tangle.safe(ps, path.events)
        if safe_events:
            return {path.extend(min(safe_events, key=sort))}

    if not kwargs["reduction"]:
        return {path.extend(p) for p in ps}
    else:
        parts = partition(U.tangle.incompatible, ps)
        branches = {min(p, key=sort) for p in parts}
        return {path.extend(b) for b in branches}


def max_paths(U, query: Optional[Query] = None, yield_xs=False, **kwargs):
    """Yield each maximal path"""
    new_paths = [Path.create_empty()]

    while new_paths:
        path = new_paths.pop()

        # Don't extend paths that resolve query
        if query and query(path, **kwargs) != None:
            yield (path, xs) if yield_xs else path
            continue

        xs = extensions(U, path, **kwargs)
        if xs:
            new_paths.extend(xs)
        else:
            yield (path, xs) if yield_xs else path
