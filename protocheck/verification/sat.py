from .precedence import (
    consistent,
    pairwise,
    and_,
    or_,
    bx,
    sequential,
    simultaneous,
    impl,
    ordered,
    reset_stats,
    stats,
    wrap,
    var,
    name,
    onehot,
)
from . import logic
from .logic import merge, onehot0
from functools import lru_cache, partial
from ..protocol import Message


@wrap(name)
def observes(role, event):
    return var(role + ":" + event)


send = observes
recv = observes


def atomic(P):
    c = correct(P)
    m = maximal(P)

    def inner(Q, r):
        formula = logic.And(c, m, enactability(r), incomplete(Q))
        return formula

    return inner


# Role
def minimality(role, protocol):
    """Every parameter observed by a role must have a corresponding
    message transmission or reception"""
    sources = {}

    def add(m, p):
        if p in sources:
            sources[p].append(m)
        else:
            sources[p] = [m]

    outgoing = set()
    for m in role.messages(protocol).values():
        if m.recipient == role:
            for p in m.ins.union(m.outs):
                add(m, p)
        else:
            for p in m.outs:
                add(m, p)
            for p in m.ins:
                outgoing.add(p)

    # keep track of 'in' parameters being sent without sources
    # unsourced parameters cannot be observed
    unsourced = [
        logic.Name(~observes(role, p), p) for p in outgoing - set(sources.keys())
    ]

    # sourced parameters must be received or sent to be observed
    sourced = [
        logic.Name(
            impl(
                observes(role, p),
                or_(
                    *[
                        simultaneous(observes(role, m), observes(role, p))
                        for m in sources[p]
                    ]
                ),
            ),
            p,
        )
        for p in sources
    ]

    return logic.And(*(unsourced + sourced))


def nonsimultaneity(self, protocol):
    msgs = [sent(m) for m in protocol.messages.values() if m.sender == self]
    if len(msgs) > 1:
        return ordered(*msgs)
    else:
        return bx.ONE


# Protocol


@lru_cache()
def is_enactable(P):
    return consistent(logic.And(correct(P), enactability(P)))


def is_live(protocol):
    return is_enactable(protocol) and not consistent(dead_end(protocol))


def is_safe(P):
    # prove there are no unsafe enactments
    return not consistent(unsafe(P))


def recursive_property(P, prop, filter=None, verbose=None):
    for r in P.references.values():
        if filter and not filter(r):
            continue  # skip references that do not pass the filter
        formula = prop(P, r)
        if verbose:
            print_formula(formula)
        s = consistent(formula)
        if s:
            # found solution; short circuit
            return s, formula
        else:
            # recurse
            s, formula = recursive_property(r, prop, filter)
            if s:
                return s, formula

    return None, None


def check_atomicity(P, args=None):
    def filter(ref):
        return type(ref) is not Message or ref.is_entrypoint

    # if args and args.exhaustive:
    #     return P.recursive_property(atomic(P))
    # else:
    return recursive_property(P, atomic(P), filter, verbose=args and args.verbose)


def is_atomic(P):
    solution, _ = check_atomicity(P)
    return not solution


def p_cover(P, parameter):
    if type(parameter) is not str:
        parameter = parameter.name

    alts = []
    for m in P.messages.values():
        if parameter in m.parameters:
            alts.append(m)
    return alts


@logic.named
def cover(P):
    return logic.And(
        *[
            logic.Name(or_(*[received(m) for m in p_cover(P, p)]), p.name + "-cover")
            for p in P.public_parameters.values()
        ]
    )


@logic.named
def unsafe(P):
    clauses = []
    for p in P.all_parameters:
        sources = [m for m in p_cover(P, p) if m.parameters[p].adornment == "out"]
        if len(sources) > 1:
            alts = []
            for r in P.roles.values():
                # assume an agent can choose between alternative messages
                msgs = [sent(m) for m in sources if m.sender == r]
                if msgs:
                    alts.append(or_(*msgs))
            # at most one message producing this parameter can be sent
            more_than_one = or_(*pairwise(and_, alts))

            # only consider cases where more than one at once is possible
            if more_than_one:
                clauses.append(logic.Name(more_than_one, p + "-unsafe"))
    if clauses:
        # at least one conflict
        return logic.And(correct(P), logic.Name(clauses, "unsafe"))
    else:
        # no conflicting pairs; automatically safe -> not unsafe
        return bx.ZERO


def enactable(P):
    "Some message must be received containing each parameter"
    clauses = []
    for p in P.public_parameters:
        clauses.append(or_(*[received(m) for m in p_cover(P, p)]))
    return and_(*clauses)


@logic.named
def enactability(P):
    return enactable(P)


@logic.named
def dead_end(protocol):
    return logic.And(correct(protocol), maximal(protocol), incomplete(protocol))


@logic.named
def correct(P):
    clauses = {}
    msgs = P.messages.values()
    roles = P.roles.values()
    clauses["Emission"] = {m.name: emission(m) for m in msgs}
    clauses["Reception"] = {m.name: reception(m) for m in msgs}
    clauses["Transmission"] = {m.name: transmission(m) for m in msgs}
    clauses["Non-lossy"] = {m.name: non_lossy(m) for m in msgs}
    clauses["Non-simultaneity"] = {r.name: nonsimultaneity(r, P) for r in roles}
    clauses["Minimality"] = {r.name: minimality(r, P) for r in roles}
    clauses["Uniqueness"] = {k: uniqueness(P, k) for k in P.keys}
    return clauses


@logic.named
def maximal(P):
    "Each message must be sent, or it must be blocked by a prior binding"
    clauses = []
    for m in P.messages.values():
        clauses.append(sent(m) | blocked(m))
    return and_(*clauses)


@logic.named
def begin(P):
    return or_(*[sent(m) for m in P.messages.values()])


def uniqueness(P, key):
    "Bindings to key parameters uniquely identify enactments, so there should never be multiple messages with the same out key in the same enactment"

    candidates = set()
    for m in P.messages.values():
        if key in m.outs:
            candidates.add(simultaneous(sent(m), observes(m.sender, key)))
    if candidates:
        return onehot0(*candidates)
    else:
        return True


def complete(P):
    "Each out parameter must be observed by at least one role"
    clauses = []
    for p in P.outs:
        clauses.append(
            or_(
                *[
                    received(m)
                    for m in p_cover(P, p)
                    if m.parameters[p].adornment == "out"
                ]
            )
        )
    return and_(*clauses)


@logic.named
def incomplete(P):
    return ~complete(P)


###### Message ######
def sent(m):
    return send(m.sender, m.qualified_name)


def received(m):
    return recv(m.recipient, m.qualified_name)


def blocked(msg):
    s = partial(observes, msg.sender)
    ins = [~s(p) for p in msg.ins]
    nils = [
        and_(s(p), ~(sequential(s(p), sent(msg)) | simultaneous(s(p), sent(msg))))
        for p in msg.nils
    ]
    outs = [s(p) for p in msg.outs]
    return or_(*(nils + outs + ins))


def transmission(msg):
    "Each message reception is causally preceded by its emission"
    return impl(received(msg), sequential(sent(msg), received(msg)))


def non_lossy(msg):
    "Each message emission results in reception"
    return impl(sent(msg), received(msg))


def emission(msg):
    """Sending a message must be preceded by observation of its ins,
    but cannot be preceded by observation of any nils or outs"""
    s = partial(observes, msg.sender)
    ins = [impl(sent(msg), sequential(s(p), sent(msg))) for p in msg.ins]
    nils = [impl(and_(sent(msg), s(p)), sequential(sent(msg), s(p))) for p in msg.nils]
    outs = [impl(sent(msg), simultaneous(s(p), sent(msg))) for p in msg.outs]
    return and_(*(ins + nils + outs))


def reception(msg):
    "Each message reception is accompanied by the observation of its parameters; either they are observed, or the message itmsg is not"
    clauses = [
        impl(
            received(msg),
            or_(sequential(p, received(msg)), simultaneous(p, received(msg))),
        )
        for p in map(partial(observes, msg.recipient), msg.ins | msg.outs)
    ]
    return and_(*clauses)


def print_formula(*formulas):
    print("\nFormula:")
    print(json.dumps(logic.merge(*formulas), default=str, sort_keys=True, indent=2))
    print()


def handle_enactability(P, args):
    reset_stats()
    e = is_enactable(P)
    print("  Enactable: ", bool(e))
    if args.verbose or args.stats:
        print("    stats: ", stats)
    if not e and not args.quiet or args.verbose:
        print_formula(logic.And(correct(P), enactability(P)))
    if e and args.verbose:
        pp.pprint(e)

    return e


def handle_liveness(protocol, args):
    reset_stats()
    e = is_enactable(protocol)
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
    expr = unsafe(protocol)
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
