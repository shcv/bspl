#!/usr/bin/env python3

import spearmint as sp
from spearmint import Experiment
import fire
from bspl.parsers import bspl
from bspl.verification.mambo import match_paths
from bspl.verification.paths import UoD
import bspl.verification.paths as tango
from bspl.generators.mambo import unsafe, nonlive

experiment = Experiment(
    name="mambo",
    parameters={
        "protocol": {
            pair[0]: bspl.load_file(pair[1]).protocols[pair[0]]
            for pair in [
                ("PO Pay Cancel Ship", "samples/tests/po-pay-cancel-ship.bspl"),
                ("Block-Contra", "samples/partial-order/block-contra.bspl"),
                ("Independent", "samples/partial-order/independent.bspl"),
                ("NetBill", "samples/netbill-bliss.bspl"),
                ("CreateOrder", "samples/lab-order"),
                # ("Sale", "samples/tests/unsafe-sale.bspl"),
            ]
        },
        "query": ["safety", "liveness"],
        "method": [
            "tango",
            "tango+",
            "mambo",
        ],
        "iteration": range(10),
    },
)

i = 100


@experiment.action(method="tango")
def check_tango(iteration=None, protocol=None, query=None, **kwargs):
    protocol = experiment.parameters["protocol"][protocol]
    if query == "safety":
        result = tango.safe(protocol)["safe"]
    elif query == "liveness":
        result = tango.live(protocol)["live"]
    return {"result": result}


@experiment.action(method="tango+")
def query_filter(iteration=None, protocol=None, query=None, **kwargs):
    protocol = experiment.parameters["protocol"][protocol]
    paths = tango.max_paths(protocol)
    if query == "safety":
        q = unsafe(protocol)
    elif query == "liveness":
        q = nonlive(protocol)
    if q:
        result = [p for p in paths if q(p)]
    else:
        result = []
    return {"result": not result}


@experiment.action(method="mambo")
def check_mambo(iteration=None, protocol=None, query=None, **kwargs):
    protocol = experiment.parameters["protocol"][protocol]
    if query == "safety":
        q = unsafe(protocol)
    elif query == "liveness":
        q = nonlive(protocol)

    if q:
        result = next(
            match_paths(protocol, q, residuate=True, prune=True, incremental=True), None
        )
    else:
        result = []
    return {"result": not result}


@experiment.postprocess
def postprocess(results):
    results["duration"] = results["duration"] * 1000
    stats = (
        results.groupby(["protocol", "query", "method", "result"])
        .agg({"duration": ["mean", "std", "min", "max", "count"]})
        .round(3)
    )
    print(stats)
    return stats


if __name__ == "__main__":
    fire.Fire(experiment)
