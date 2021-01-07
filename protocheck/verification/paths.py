from ..protocol import Message, Role, Parameter


def empty_path():
    """The empty path is a list with no message instances"""
    return tuple()


External = Role("*External*")


class Instance():
    def __init__(self, msg, delay=float('inf')):
        self.msg = msg
        self.delay = delay

    def __str__(self):
        return "<{},{}>".format(self.msg.name, self.delay)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.msg == other.msg and self.delay == other.delay
        else:
            return False

    def __hash__(self):
        return (self.msg, self.delay).__hash__()

    @property
    def received(self):
        return self.delay < float('inf')


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
        if (set(instance.msg.parameters) >= set(keys)
            and (instance.msg.sender.name == R.name
                 or (instance.msg.recipient.name == R.name
                     and instance.delay + time <= len(path)))):
            k.update(set(instance.msg.ins))
            k.update(set(instance.msg.outs))
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
    # print(msg.keys)
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


class UoD():
    def __init__(self, messages={}, roles={}):
        self.messages = set(messages)
        self.roles = set(roles)

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


def branches(U, path):
    b = set()
    for msg in U.messages:
        # print(msg.name, viable(path, msg))
        if viable(path, msg):
            # default messages to unreceived, progressively receive them later
            inst = Instance(msg, float("inf"))
            if msg.sender == External:
                inst.delay = 0
            b.add(inst)
    return b


def unreceived(path):
    return set(i for i in path if i.delay == float("inf"))


def any_unreceived(path):
    for i in path:
        if i.delay == float('inf'):
            return True


def receive(path, instance):
    p = list(path)
    i = p.index(instance)
    p[i] = Instance(instance.msg, len(p) - i - 1)
    return tuple(p)


def extensions(U, path):
    xs = {path + (b,) for b in branches(U, path)}
    return xs.union({receive(path, u) for u in unreceived(path)})


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
    new_paths = [empty_path()]
    while len(new_paths):
        p = new_paths.pop()
        xs = extensions(U, p)
        if xs:
            new_paths.extend(xs)
        else:
            if total_knowledge(U, p).intersection(protocol.outs) < protocol.outs:
                return {"live": False,
                        "reason": "Found path that does not extend to completion",
                        "path": p}
    return {"live": True}


def path_safety(protocol, args=None):
    U = UoD.from_protocol(protocol)
    parameters = {p for m in protocol.messages.values() for p in m.outs}
    new_paths = [empty_path()]
    count = 0
    while len(new_paths):
        path = new_paths.pop()
        xs = extensions(U, path)
        if xs:
            new_paths.extend(xs)
        for p in parameters:
            if len(sources(path, p)) > 1:
                return {"safe": False,
                        "reason": "Found parameter with multiple sources in a path",
                        "path": path,
                        "parameter": p}
    return {"safe": True}


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
        if len(p) > len(U.messages):
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
