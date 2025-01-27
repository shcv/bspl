#!/usr/bin/env python3

import spearmint as sp
from spearmint import Experiment
import fire
from pprint import pformat
from bspl.parsers import bspl, precedence
from bspl.verification.mambo import match_paths, QuerySemantics, Any
from bspl.verification.paths import UoD
import bspl.verification.paths as tango
from bspl.generators.mambo import unsafe, nonlive

from bspl.verification import paths as tango
from bspl.verification import mambo

Sale = bspl.load_file("samples/sale.bspl").protocols["Sale"]

experiment = Experiment(
    name="mambo-props",
    parameters={
        "iteration": range(10),
        "property": {
            "live": {"expected": "all", "query": -nonlive(Sale)},
            "safe": {"expected": "all", "query": -unsafe(Sale)},
            "desired-end": {
                "expected": "all",
                "query": "rescindAck or reject or transfer and (refund or deliver)",
            },
            "create-detach-discharge": {
                "expected": "some",
                "query": "offer . accept and offer . transfer and accept . deliver and transfer . deliver",
            },
            "flexibility": {
                "expected": "some",
                "query": "accept . deliver and deliver . transfer",
            },
            "delegation-guarantee": {
                "expected": "all",
                "query": "no pay and no transfer or pay . transfer",
            },
            "concede": {
                "expected": "all",
                "query": "pay . Buyer:rescind or (no rescind and no rescindAck) or rescind . rescindAck",
            },
            "late-action": {
                "expected": "all",
                "query": "no accept or no rescind or accept . Buyer:rescind",
            },
            "compensation": {
                "expected": "all",
                "query": "(no transfer or deliver or refund) and (no refund or transfer) and (no refund or no deliver)",
            },
            "complementary": {"expected": "none", "query": "reject and deliver"},
            "deadwood": {"expected": "none", "query": "deadwood"},
        },
    },
)

properties = experiment.parameters["property"]


@experiment.action
def check_mambo(iteration=None, property=None, **kwargs):
    if property == "deadwood":
        dead = mambo.deadwood(Sale)
        return {"satisfied": not dead}
    criteria = properties[property]["expected"]
    q = precedence.parse(properties[property]["query"], semantics=QuerySemantics())

    if criteria == "all":
        # negate query to prove that none match the negation
        q = -q

    result = list(
        match_paths(
            Sale,
            q,
            residuate=True,
            prune=True,
            incremental=True,
            safe=True,
            # verbose=True,
            # max_only=True,
        )
    )

    if criteria == "all":
        return {"satisfied": not result}
    if criteria == "some":
        return {"satisfied": bool(result)}
    if criteria == "none":
        return {"satisfied": not bool(result)}


@experiment.postprocess
def postprocess(results):
    results["duration"] = results["duration"] * 1000
    stats = (
        results.groupby(["property", "satisfied"])
        .agg({"duration": ["mean", "std", "min", "max", "count"]})
        .round(3)
    )
    print(stats)
    return stats


if __name__ == "__main__":
    fire.Fire(experiment)
