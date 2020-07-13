from .precedence import consistent, pairwise,     \
    and_, or_, bx, sequential, simultaneous, impl, ordered, \
    reset_stats, stats, wrap, var, name, onehot
from . import logic
from .logic import merge, onehot0


@wrap(name)
def observe(role, event):
    return var(role + ":" + event)


send = observe
recv = observe


def atomic(p):
    c = p.correct
    m = p.maximal

    def inner(q, r):
        formula = logic.And(c, m,
                            r.enactability,
                            q.incomplete)
        return formula
    return inner


# Role
def minimality(self, protocol):
    """Every parameter observed by a role must have a corresponding
    message transmission or reception"""
    sources = {}

    def add(m, p):
        if p in sources:
            sources[p].append(m)
        else:
            sources[p] = [m]

    outgoing = set()
    for m in self.messages(protocol).values():
        if m.recipient == self:
            for p in m.ins.union(m.outs):
                add(m, p)
        else:
            for p in m.outs:
                add(m, p)
            for p in m.ins:
                outgoing.add(p)

    # keep track of 'in' parameters being sent without sources
    # unsourced parameters cannot be observed
    unsourced = [logic.Name(~self.observe(p), p)
                 for p in outgoing - set(sources.keys())]

    # sourced parameters must be received or sent to be observed
    sourced = [logic.Name(impl(self.observe(p),
                               or_(*[simultaneous(self.observe(m), self.observe(p))
                                     for m in sources[p]])),
                          p)
               for p in sources]

    return logic.And(*(unsourced + sourced))


def nonsimultaneity(self, protocol):
    msgs = [m.sent for m in protocol.messages.values() if m.sender == self]
    if len(msgs) > 1:
        return ordered(*msgs)
    else:
        return bx.ONE

# Protocol


def is_enactable(protocol):
    if self.enactable is None:
        self.enactable = consistent(
            logic.And(self.correct, self.enactability))
    return self.enactable


def is_live(self):
    return self.is_enactable() and not consistent(self.dead_end)


def is_safe(self):
    # prove there are no unsafe enactments
    return not consistent(self.unsafe)


def recursive_property(self, prop, filter=None, verbose=None):
    for r in self.references:
        if filter and not filter(r):
            continue  # skip references that do not pass the filter
        formula = prop(self, r)
        if verbose:
            print_formula(formula)
        s = consistent(formula)
        if s:
            # found solution; short circuit
            return s, formula
        else:
            # recurse
            s, formula = r.recursive_property(prop, filter)
            if s:
                return s, formula

    return None, None


def check_atomicity(self, args=None):
    def filter(ref):
        return type(ref) is not Message or ref.is_entrypoint

    # if args and args.exhaustive:
    #     return self.recursive_property(atomic(self))
    # else:
    return self.recursive_property(atomic(self), filter, verbose=args and args.verbose)


def is_atomic(self):
    solution, _ = self.check_atomicity()
    return not solution


def p_cover(self, parameter):
    if type(parameter) is not str:
        parameter = parameter.name

    alts = []
    for m in self.messages.values():
        if parameter in m.parameters:
            alts.append(m)
    return alts


@property
@logic.named
def cover(self):
    return logic.And(*[logic.Name(or_(*[m.received for m in self.p_cover(p)]),
                                  p.name + "-cover")
                       for p in self.public_parameters.values()])


@property
@logic.named
def unsafe(self):
    clauses = []
    for p in self.all_parameters:
        sources = [m for m in self.p_cover(p)
                   if m.parameters[p].adornment == 'out']
        if len(sources) > 1:
            alts = []
            for r in self.roles.values():
                # assume an agent can choose between alternative messages
                msgs = [m.sent for m in sources if m.sender == r]
                if msgs:
                    alts.append(or_(*msgs))
            # at most one message producing this parameter can be sent
            more_than_one = or_(*pairwise(and_, alts))

            # only consider cases where more than one at once is possible
            if more_than_one:
                clauses.append(
                    logic.Name(more_than_one, p + "-unsafe"))
    if clauses:
        # at least one conflict
        return logic.And(self.correct, logic.Name(clauses, "unsafe"))
    else:
        # no conflicting pairs; automatically safe -> not unsafe
        return bx.ZERO


def _enactable(self):
    "Some message must be received containing each parameter"
    clauses = []
    for p in self.public_parameters:
        clauses.append(or_(*[m.received for m in self.p_cover(p)]))
    return and_(*clauses)


@property
@logic.named
def enactability(self):
    return self._enactable()


@property
@logic.named
def unenactable(self):
    return ~self._enactable()


@property
@logic.named
def dead_end(self):
    return logic.And(self.correct, self.maximal, self.incomplete)


@property
@logic.named
def correct(self):
    clauses = {}
    msgs = self.messages.values()
    roles = self.roles.values()
    clauses["Emission"] = {m.name: m.emission for m in msgs}
    clauses["Reception"] = {m.name: m.reception for m in msgs}
    clauses["Transmission"] = {m.name: m.transmission for m in msgs}
    clauses["Non-lossy"] = {m.name: m.non_lossy for m in msgs}
    clauses["Non-simultaneity"] = {r.name: r.nonsimultaneity(self)
                                   for r in roles}
    clauses["Minimality"] = {r.name: r.minimality(self) for r in roles}
    clauses["Uniqueness"] = {k: self.uniqueness(k) for k in self.keys}
    return clauses


@property
@logic.named
def maximal(self):
    "Each message must be sent, or it must be blocked by a prior binding"
    clauses = []
    for m in self.messages.values():
        clauses.append(m.sent | m.blocked)
    return and_(*clauses)


@property
@logic.named
def begin(self):
    return or_(*[m.sent for m in self.messages.values()])


def uniqueness(self, key):
    "Bindings to key parameters uniquely identify enactments, so there should never be multiple messages with the same out key in the same enactment"

    candidates = set()
    for m in self.messages.values():
        if key in m.outs:
            candidates.add(simultaneous(
                m.sent, observe(m.sender, key)))
    if candidates:
        return onehot0(*candidates)
    else:
        return True


def _complete(self):
    "Each out parameter must be observed by at least one role"
    clauses = []
    for p in self.outs:
        clauses.append(or_(*[m.received for m in self.p_cover(p)
                             if m.parameters[p].adornment is 'out']))
    return and_(*clauses)


@property
@logic.named
def complete(self):
    return self._complete()


@property
@logic.named
def incomplete(self):
    return ~self._complete()


###### Message ######
@property
def sent(self):
    return send(self.sender, self.name)


@property
def received(self):
    return recv(self.recipient, self.name)


@property
@logic.named
def enactability(self):
    return self.received


def check_atomicity(self):
    return None, None


@property
@logic.named
def unenactable(self):
    return ~self.received


@property
def blocked(self):
    s = partial(observe, self.sender)
    ins = [~s(p) for p in self.ins]
    nils = [and_(s(p), ~(sequential(s(p), self.sent) |
                         simultaneous(s(p), self.sent))) for p in self.nils]
    outs = [s(p) for p in self.outs]
    return or_(*(nils + outs + ins))


@property
def transmission(self):
    "Each message reception is causally preceded by its emission"
    return impl(self.received, sequential(self.sent, self.received))


@property
def non_lossy(self):
    "Each message emission results in reception"
    return impl(self.sent, self.received)


@property
def emission(self):
    """Sending a message must be preceded by observation of its ins,
       but cannot be preceded by observation of any nils or outs"""
    s = partial(observe, self.sender)
    ins = [impl(self.sent, sequential(s(p), self.sent))
           for p in self.ins]
    nils = [impl(and_(self.sent, s(p)), sequential(self.sent, s(p)))
            for p in self.nils]
    outs = [impl(self.sent, simultaneous(s(p), self.sent))
            for p in self.outs]
    return and_(*(ins + nils + outs))


@property
def reception(self):
    "Each message reception is accompanied by the observation of its parameters; either they are observed, or the message itself is not"
    clauses = [impl(self.received,
                    or_(sequential(p, self.received),
                        simultaneous(p, self.received)))
               for p in map(partial(observe, self.recipient), self.ins | self.outs)]
    return and_(*clauses)


def print_formula(*formulas):
    print("\nFormula:")
    print(json.dumps(logic.merge(*formulas),
                     default=str, sort_keys=True, indent=2))
    print()


def handle_enactability(protocol, args):
    reset_stats()
    e = protocol.is_enactable()
    print("  Enactable: ", bool(e))
    if args.verbose or args.stats:
        print("    stats: ", stats)
    if not e and not args.quiet or args.verbose:
        print_formula(logic.And(protocol.correct, protocol.enactability))
    if e and args.verbose:
        pp.pprint(e)

    return e


def handle_liveness(protocol, args):
    reset_stats()
    e = protocol.is_enactable()
    violation = consistent(protocol.dead_end)
    print("  Live: ", e and not violation)
    if args.verbose or args.stats:
        print("    stats: ", stats)
    if violation and not args.quiet or args.verbose:
        print_formula(protocol.dead_end)
    if violation and not args.quiet:
        print("\n    Violation:")
        pp.pprint(violation)
        print()


def handle_safety(protocol, args):
    reset_stats()
    expr = protocol.unsafe
    violation = consistent(expr)
    print("  Safe: ", not violation)
    if args.verbose or args.stats:
        print("    stats: ", stats)
    if violation and not args.quiet or args.verbose:
        print_formula(expr)
    if violation and not args.quiet:
        print("\nViolation:")
        pp.pprint(violation)
        print()


def handle_atomicity(protocol, args):
    reset_stats()
    a, formula = protocol.check_atomicity(args)
    print("  Atomic: ", not a)
    if args.verbose or args.stats:
        print("    stats: ", stats)
    if a and not args.quiet:
        print("\nViolation:")
        pp.pprint(a)
        print("\nFormula:")
        print(json.dumps(formula, default=str, sort_keys=True, indent=2))
        print()
