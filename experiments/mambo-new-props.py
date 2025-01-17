#!/usr/bin/env python3

import spearmint as sp
from spearmint import Experiment
import fire
from bspl.parsers import bspl, precedence
from bspl.verification.mambo import match_paths, QuerySemantics
from bspl.verification.paths import UoD
import bspl.verification.paths as tango
from bspl.generators.mambo import unsafe, nonlive

Sale = bspl.load_file("samples/sale.bspl").protocols["Sale"]

experiment = Experiment(
    name="mambo",
    parameters={
        "query": {
            "nonlive": nonlive(Sale),
            "unsafe": unsafe(Sale),
            "desired-end": "rescindAck or reject or transfer and (refund or deliver)",
            "create-detach-discharge": "offer . accept and offer . transfer and accept . deliver and transfer . deliver",
            "flexibility": "accept . deliver and deliver . transfer", 
            "delegation-guarantee": "no pay and no transfer or pay . transfer",
            "concede": "pay . Buyer:rescind or (no rescind and no rescindAck) or rescind . rescindAck",
            "complementary": "pay and rescindAck", 
            "late-action": "no accept or no rescind or accept . Buyer:rescind",
            "compensation": "(no transfer or deliver or refund) and (no refund or transfer) and (no refund or no deliver)",
            "nonexclusive": "reject and deliver",
        },
        "iteration": range(1),
    },
)


@experiment.action
def check_mambo(iteration=None, query=None, **kwargs):
    q = experiment.parameters["query"][query]
    print(f"{query}: {precedence.parse(q, semantics=QuerySemantics())}")
    result = list(match_paths(Sale, q, residuate=True, prune=True, incremental=True))
    nresult = list(
        match_paths(Sale, f"no ({q})", residuate=True, prune=True, incremental=True)
    )
    if nresult:
        print("\n".join([str(p.events) for p in nresult]))
        print()
    return {"result": (len(result), len(nresult))}


@experiment.postprocess
def postprocess(results):
    results["duration"] = results["duration"] * 1000
    stats = (
        results.groupby(["query", "result"])
        .agg({"duration": ["mean", "std", "min", "max", "count"]})
        .round(3)
    )
    print(stats)
    # return stats


if __name__ == "__main__":
    fire.Fire(experiment)
