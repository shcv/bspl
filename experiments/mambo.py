#!/usr/bin/env python3

import spearmint as sp
from spearmint import Experiment
import fire
from bspl.parsers import bspl
from bspl.verification.mambo import match_paths
from bspl.verification.paths import UoD
from bspl.generators.mambo import unsafe, nonlive

experiment = Experiment(
    name="mambo",
    parameters={
        "protocol": [
            p
            for f in [
                "samples/ebusiness.bspl",
                # "samples/netbill.bspl",
                # "samples/tests/nonlive-indirect",
                "samples/Ebusiness-Four-Party.bspl",
            ]
            for p in bspl.load_file(f).protocols.values()
        ],
        "query": ["safety", "liveness"],
        "residuate": [False, True],
        "prune": [False, True],
        "incremental": [False, True],
        "iteration": range(10),
    },
)


@experiment.action(query="safety")
def check_safety(iteration=None, protocol=None, **kwargs):
    q = unsafe(protocol)
    if q:
        U = UoD.from_protocol(protocol, conflicts=q.conflicts)
        result = next(
            match_paths(
                U,
                q,
                **{k: kwargs.get(k) for k in ["residuate", "prune", "incremental"]}
            ),
            None,
        )
    else:
        result = []
    return {"result": not result, "protocol": protocol.name}


@experiment.action(query="liveness")
def check_liveness(iteration=None, protocol=None, **kwargs):
    q = nonlive(protocol)
    if q:
        U = UoD.from_protocol(protocol, conflicts=q.conflicts)
        result = next(
            match_paths(
                U,
                q,
                **{k: kwargs.get(k) for k in ["residuate", "prune", "incremental"]}
            ),
            None,
        )
        # if result:
        # print(result)
    else:
        result = []
    return {"result": not result, "protocol": protocol.name}


@experiment.preprocess
def preprocess(exp):
    """Preprocess the experiment, mutating keys and results in place"""
    for k in exp.keys:
        k["protocol"] = k["protocol"].name
    for r in exp.results:
        del r["protocol"]


@experiment.postprocess
def postprocess(results):
    results["duration"] = results["duration"] * 1000
    stats = (
        results.groupby(["protocol", "query", "residuate", "prune", "incremental"])
        .agg({"duration": ["mean", "std", "min", "max", "count"]})
        .round(3)
    )
    print(stats)
    # return stats


if __name__ == "__main__":
    fire.Fire(experiment)
