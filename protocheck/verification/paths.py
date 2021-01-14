from ..protocol import Message, Role, Parameter


def empty_path():
    """The empty path is a list with no message instances"""
    return tuple()


External = Role("*External*")


class Emission:
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return f"{self.sender.name}!{self.msg.name}"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.msg == other.msg
        else:
            return False

    def __hash__(self):
        return (self.msg).__hash__()

    def __getattr__(self, attr):
        return getattr(self.msg, attr)


def key_sets(path):
    keys = set()
    for i in path:
        keys.add(tuple(i.msg.keys))
    return keys


def known(path, keys, R):
    """Compute the set of parameters observed by role R after enacting path"""
    time = 0
    k = set()
    for instance in path:
        if (set(instance.msg.parameters).intersection(set(keys))
            and (isinstance(instance, Emission) and instance.sender.name == R.name
                 or (isinstance(instance, Reception) and instance.recipient.name == R.name))):
            k.update(instance.ins)
            k.update(instance.outs)
        time += 1
    return k


def sources(path, p):
    """The set of all roles that produce p as an out parameter in path"""
    return set(i.msg.sender.name for i in path if p in i.msg.outs)


def viable(path, msg):
    msg_count = len([i.msg for i in path if i.msg == msg])
    if not msg.ins.union(msg.nils).symmetric_difference({p.name for p in msg.parameters.values()}) and msg_count > 0:
        # only allow one copy of an all "in"/"nil" message
        # print("Only one copy of all in message allowed")
        return False
    if msg.sender == External:
        # only send external messages if they would contribute
        k = known(path, (), msg.recipient)
        if not k.issuperset(msg.ins):
            return True
        else:
            print("Only send external messages if they would contribute")
            return False
    out_keys = set(msg.keys).intersection(msg.outs)
    # print(msg.name)
    # print(msg.keys, msg.outs, out_keys)
    # print(msg.outs)
    # print(out_keys)
    if out_keys and all(sources(path, p) for p in out_keys):
        # don't allow multiple key bindings in the same path; they're different enactments
        # print("Don't allow multiple key bindings on the same path; they're different enactments")
        return False
    k = known(path, msg.keys, msg.sender)
    return k.issuperset(msg.ins) \
        and k.isdisjoint(msg.outs) \
        and k.isdisjoint(msg.nils)


def disables(a, b):
    "Return true if message a directly disables message b"
    for p in a.outs.union(a.ins):
        # out or in disables out or nil
        if p in b.parameters:
            if b.parameters[p].adornment in ['out', 'nil']:
                return True


def enables(a, b):
    "Return true if message a directly enables message b"
    if not disables(a, b):
        # out enables in
        for p in a.outs:
            if p in b.parameters:
                if b.parameters[p].adornment == 'in':
                    return True


class Tangle():
    "Graph representation of entanglements between messages"

    def __init__(self, messages):
        self.emissions = {Emission(m) for m in messages}
        self.receptions = {Reception(e) for e in self.emissions}

        # initialize graph with direct enable and disablements, O(m^2)
        self.enables = {a: {b for b in messages
                            if a != b and enables(a, b)}
                        for a in messages}
        self.disables = {a: {b for b in messages
                             if a != b and disables(a, b)}
                         for a in messages}

        # sources for parameters, for computing endowment
        self.sources = {}
        for m in messages:
            for p in m.outs:
                if p not in self.sources:
                    self.sources[p] = [m]
                else:
                    self.sources[p].append(m)

        # track messages that are the sole source of a given parameter
        self.source = {p: ms[0]
                       for p, ms in self.sources.items() if len(ms) == 1}

        # a endows b if a is the sole source of an 'in' parameter of b
        self.endows = {}
        for b in messages:
            for p in b.ins:
                a = self.source.get(p)
                if not a:
                    continue
                if a in self.endows:
                    self.endows[a].add(b)
                else:
                    self.endows[a] = {b}

        # propagate enablements; a |- b & b |- c => a |- c
        def enablees(m):
            es = self.enables[m]
            return es.union(*[enablees(b) for b in es])

        for m, es in self.enables.items():
            es.update(enablees(m))

        # compute entanglements:
        # a -|| c if:
        #  1. a does not endow c
        #  2. a -| c or a -| b and c |- b
        self.tangles = {a: self.disables[a]
                        .union({c for c in self.enables
                                if c not in self.endows.get(a, [])
                                and self.enables[c].intersection(self.disables[a])})
                        for a in messages}

        # incompatibility graph
        # a and b are incompatible if
        #  1. one is an emission (TODO)
        #  2. one tangles with the other
        self.incompatible = {m: set() for m in messages}
        for a in self.tangles:
            self.incompatible[a].update(self.tangles[a])
            for b in self.tangles[a]:
                self.incompatible[b].add(a)


class UoD():
    def __init__(self, messages=set(), roles={}):
        self.messages = set(messages)
        self.roles = set(roles)
        self.tangle = Tangle(messages)

    @staticmethod
    def from_protocol(protocol):
        if not protocol.ins.union(protocol.nils):
            return UoD(list(protocol.messages.values()), protocol.roles.values())
        else:
            dependencies = {}
            for r in protocol.roles.values():
                if r.name is External.name:
                    continue
                keys = protocol.ins.intersection(protocol.keys)
                # generate messages that provide p to each sender
                msg = Message(
                    'external->{r.name}',
                    External,
                    r,
                    [Parameter(k, 'in', True) for k in keys]
                    + [Parameter(p, 'in')
                       for p in protocol.ins.difference(keys)]
                )
                dependencies[r.name] = msg
            # hmmm; probably shouldn't modify protocol...
            protocol.roles[External.name] = External
            uod = UoD(list(protocol.messages.values()) + list(dependencies.values()),
                      protocol.roles.values())
            return uod

    def __add__(self, other):
        return UoD(self.messages.union(other.messages), self.roles.union(other.roles))


class Reception:
    def __init__(self, emission):
        self.emission = emission
        self.msg = emission.msg

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.msg == other.msg
        else:
            return False

    def __hash__(self):
        return hash(self.msg)

    def __getattr__(self, attr):
        return getattr(self.emission, attr)

    def __repr__(self):
        return f"{self.recipient.name}?{self.msg.name}"


def unreceived(path):
    sent = set(e for e in path if isinstance(e, Emission))
    received = set(r.emission for r in path if isinstance(r, Reception))
    return sent.difference(received)


def possibilities(U, path):
    b = set()
    for msg in U.messages:
        if viable(path, msg):
            # default messages to unreceived, progressively receive them later
            inst = Emission(msg)
            b.add(inst)
    ps = b.union(Reception(e) for e in unreceived(path))
    return ps


def any_unreceived(path):
    return len(unreceived(path)) > 0


class Color(set):
    def __hash__(self):
        return id(self)


def partition(graph, ps):
    """
    Partition a set of possibilities into incompatible subsets.
      graph: a dictionary from a vertex to its set of neighbors
      ps: a list of possibilities"""

    # alias graph to neighbors for readability
    neighbors = graph

    def degree(m):
        return len(neighbors[m.msg])

    # Sort vertices by degree in descending order
    vs = sorted(ps, key=degree, reverse=True)

    parts = set()
    coloring = {}
    for vertex in vs:
        # Assign a color to each vertex that isn’t assigned to its neighbors
        options = parts.difference(
            {coloring.get(n) for n in neighbors[vertex.msg]})

        # generate a new color if necessary
        if not len(options):
            color = Color()
            parts.add(color)
        elif len(options) > 1:
            # Choose a color that
            #  (1) has the highest cardinality (number of vertices)
            max_cardinality = max(len(c) for c in parts)
            options = {o for o in options if len(o) == max_cardinality}

            #  (2) within such, the color whose vertex of highest degree has the smallest degree
            if len(options) > 1:
                def max_degree(color):
                    return max(degree(v) for v in color)

                min_max = min(max_degree(c) for c in parts)
                options = {o for o in options if max_degree(o) == min_max}

            # choose color from options (randomly?)
            color = next(o for o in options)
        else:
            color = next(o for o in options)

        # color vertex
        color.add(vertex)
        coloring[vertex.msg] = color

    return parts


def extensions(U, path):
    parts = partition(U.tangle.incompatible, possibilities(U, path))
    branches = {min(p, key=lambda p: p.name) for p in parts}
    xs = {path + (b,) for b in branches}
    return xs


def max_paths(U):
    max_paths = []
    new_paths = [empty_path()]
    while len(new_paths):
        p = new_paths.pop()
        xs = extensions(U, p)
        if xs:
            new_paths.extend(xs)
        else:
            max_paths.insert(len(max_paths), p)
    return max_paths


def path_liveness(protocol, args=None):
    U = UoD.from_protocol(protocol)
    if args.verbose:
        print(f"Incompatibilities: {U.tangle.incompatible}")
    new_paths = [empty_path()]
    checked = 0
    while len(new_paths):
        p = new_paths.pop()
        checked += 1
        if args.verbose:
            print(p)
        xs = extensions(U, p)
        if xs:
            new_paths.extend(xs)
        else:
            if total_knowledge(U, p).intersection(protocol.outs) < protocol.outs:
                return {"live": False,
                        "reason": "Found path that does not extend to completion",
                        "path": p,
                        "checked": checked}
    return {"live": True, "checked": checked}


def path_safety(protocol, args=None):
    U = UoD.from_protocol(protocol)
    if args.verbose:
        print(f"Incompatibilities: {U.tangle.incompatible}")
    parameters = {p for m in protocol.messages.values() for p in m.outs}
    new_paths = [empty_path()]
    checked = 0
    while len(new_paths):
        path = new_paths.pop()
        checked += 1
        if args.verbose:
            print(path)
        xs = extensions(U, path)
        if xs:
            new_paths.extend(xs)
        for p in parameters:
            if len(sources(path, p)) > 1:
                return {"safe": False,
                        "reason": "Found parameter with multiple sources in a path",
                        "path": path,
                        "parameter": p,
                        "checked": checked}
    return {"safe": True, "checked": checked}


def total_knowledge(U, path):
    k = set()
    for r in U.roles:
        for keys in key_sets(path):
            k.update(known(path, keys, r))
    return k


def all_paths(U, verbose=False):
    paths = set()
    new_paths = {empty_path()}
    longest_path = 0
    while new_paths:
        p = new_paths.pop()
        if len(p) > longest_path:
            longest_path = len(p)
        if len(p) > len(U.messages)*2:
            print("Path too long: ", p)
            exit(1)
        xs = extensions(U, p)
        if xs:
            new_paths.update(xs)
        paths.add(p)  # add path to paths even if it has unreceived messages
        if verbose:
            if len(paths) % 10 == 0:
                print("\r{} paths, longest path: {}, unprocessed: {}".format(
                    len(paths), longest_path, len(new_paths)), end='')
            if len(paths) % 1000 == 0:
                print(p)
    if verbose:
        print()
    return paths
