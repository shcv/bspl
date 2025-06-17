#!/usr/bin/env python3

from bspl.parsers.bspl import load_file
from bspl.verification.mambo import Occurs
from itertools import combinations, chain


def unsafe(protocol):
    sources = {
        p: {m for m in protocol.messages.values() if p in m.outs}
        for p in protocol.parameters
    }
    conflicts = set(tuple(sources[p]) for p in sources if len(sources[p]) > 1)
    if not conflicts:
        return None
    # safety = not ((m1 and m2) or (m3 and m4) ...) for all pairs of conflicting messages
    # compute And(m1, m2) for all pairs of conflicting messages

    pairs = set(chain.from_iterable(combinations(c, 2) for c in conflicts))
    pairs = [
        (Occurs(p[0].name) & Occurs(p[1].name))
        for p in pairs
        if p[0].sender != p[1].sender
    ]
    if not pairs:
        return None

    # compute disjunction of all pairs
    clause = pairs[0]
    for p in pairs[1:]:
        clause = clause | p
    return clause


def nonlive(protocol):
    outs = list(protocol.outs)
    expr = ~Occurs(outs[0])
    for o in outs[1:]:
        expr = expr | ~Occurs(o)
    return expr


class MamboGenerator:
    def unsafe(self, path, protocol=None):
        spec = load_file(path)
        if protocol:
            Ps = [spec.protocols[protocol]]
        else:
            Ps = spec.protocols.values()

        for P in Ps:
            conjs = unsafe(P)
            if conjs:
                yield f"{P.name}: {conjs}"
            else:
                yield f"{P.name}: safe"

    def nonlive(self, path, protocol=None):
        """Protocols are non-live if any of the out parameters are unbound"""
        spec = load_file(path)
        if protocol:
            Ps = [spec.protocols[protocol]]
        else:
            Ps = spec.protocols.values()

        for P in Ps:
            expr = nonlive(P)
            yield f"{P.name}: {expr}"
