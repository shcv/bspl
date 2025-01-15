#!/usr/bin/env python3

from bspl.parsers.bspl import load_file
from bspl.verification.mambo import Occurs
from itertools import combinations, chain


def unsafe(protocol):
    sources = {
        p: {m.name for m in protocol.messages.values() if p in m.outs}
        for p in protocol.parameters
    }
    conflicts = set(tuple(sources[p]) for p in sources if len(sources[p]) > 1)
    if not conflicts:
        return None
    # safety = not ((m1 and m2) or (m3 and m4) ...) for all pairs of conflicting messages
    # compute And(m1, m2) for all pairs of conflicting messages
    pairs = list(
        chain.from_iterable(combinations([Occurs(m) for m in c], 2) for c in conflicts)
    )
    # compute disjunction of all pairs
    clause = pairs[0][0] & pairs[0][1]
    for p in pairs[1:]:
        clause = clause | (p[0] & p[1])
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
