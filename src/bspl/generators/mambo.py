#!/usr/bin/env python3

from bspl.parsers.bspl import load_file
from bspl.verification.mambo import Query, Or, Not, And, occurs
from itertools import combinations, chain


class MamboGenerator:
    def unsafe(self, path, protocol=None):
        spec = load_file(path)
        if protocol:
            Ps = [spec.protocols[protocol]]
        else:
            Ps = spec.protocols.values()

        for P in Ps:
            sources = {
                p: {m.name for m in P.messages.values() if p in m.outs}
                for p in P.parameters
            }
            conflicts = [sources[p] for p in sources if len(sources[p]) > 1]
            if not conflicts:
                yield f"{P.name}: safe"
                continue
            # safety = not ((m1 and m2) or (m3 and m4) ...) for all pairs of conflicting messages
            # compute And(m1, m2) for all pairs of conflicting messages
            pairs = list(
                chain.from_iterable(
                    combinations([Query(occurs, m) for m in c], 2) for c in conflicts
                )
            )
            # compute disjunction of all pairs
            conjs = Query(And, pairs[0][0], pairs[0][1])
            for p in pairs[1:]:
                conjs = Query(Or, disjuncts, Query(And, p[0], p[1]))
            yield f"{P.name}: {conjs}"

    def nonlive(self, path, protocol=None):
        """Protocols are non-live if any of the out parameters are unbound"""
        spec = load_file(path)
        if protocol:
            Ps = [spec.protocols[protocol]]
        else:
            Ps = spec.protocols.values()

        for P in Ps:
            outs = list(P.outs)
            expr = Query(occurs, outs[0])
            for o in outs[1:]:
                expr = Query(Or, expr, Query(occurs, o))
            yield f"{P.name}: {Query(Not, expr)}"
