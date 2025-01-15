#!/usr/bin/env python3

import spearmint as sp
from spearmint import Experiment
import fire
from bspl.parsers import bspl
from bspl.verification.mambo import match_paths
from bspl.verification.paths import UoD
import bspl.verification.paths as tango
from bspl.generators.mambo import unsafe, nonlive

Sale = bspl.load_file("samples/sale.bspl").protocols["Sale"]

experiment = Experiment(
    name="mambo",
    parameters={
        "query": {
            "liveness": nonlive(Sale),
            "safety": unsafe(Sale),
            "desired-end": "rescindAck ∨ reject ∨ transfer ∧ (refund ∨ deliver)",
            "happy": "offer · accept · transfer · deliver",
            "unhappy-1": "offer . accept . rescind . rescindAck",
            "unhappy-2": "offer . reject",
            "late-action": "no accept ∨ accept · rescind",
            "disables": "rescind . accept",
            "alternatives": "transfer . deliver or transfer . refund",
            "priority": "no Buyer:rescind ∨ Buyer:pay ∨ rescindAck",
            "compensation": "(no transfer ∨ deliver ∨ refund) ∧ (no refund ∨ transfer) ∧ (no refund ∨ no deliver)",
            "complementary": "reject and deliver",
            "delegation-guarantee": "(pay | transfer) | no pay . transfer",
        },
        "iteration": range(10),
    },
)


@experiment.action
def check_mambo(iteration=None, query=None, **kwargs):
    q = experiment.parameters["query"][query]
    result = list(match_paths(Sale, q, residuate=True, prune=True, incremental=True))
    return {"result": len(result)}


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
