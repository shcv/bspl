#!/usr/bin/env python3

import spearmint as sp
from spearmint import Experiment
import fire
from bspl.parsers import bspl
from bspl.verification.mambo import match_paths
from bspl.verification.paths import UoD
import bspl.verification.paths as tango
from bspl.generators.mambo import unsafe, nonlive
import numpy as np
import pandas as pd
import scipy

experiment = Experiment(
    name="mambo-comparison",
    parameters={
        "iteration": range(10),
        "protocol": {
            "PO Pay Cancel Ship": "samples/tests/po-pay-cancel-ship.bspl",
            "Block-Contra": "samples/partial-order/block-contra.bspl",
            "Independent": "samples/partial-order/independent.bspl",
            "NetBill": "samples/netbill-bliss.bspl",
            "CreateOrder": "samples/fixed-lab-order",
            "Sale": "samples/sale.bspl",
        },
        "query": ["safety", "liveness"],
        "method": [
            "tango",
            "tango+",
            "mambo",
        ],
    },
)

protocols = experiment.parameters["protocol"]


@experiment.action(method="tango")
def check_tango(iteration=None, protocol=None, query=None, **kwargs):
    protocol = bspl.load_file(protocols[protocol]).protocols[protocol]
    if query == "safety":
        result = tango.safe(protocol)["safe"]
    elif query == "liveness":
        result = tango.live(protocol)["live"]
    return {"result": result}


@experiment.action(method="tango+")
def query_filter(iteration=None, protocol=None, query=None, **kwargs):
    protocol = bspl.load_file(protocols[protocol]).protocols[protocol]
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
    protocol = bspl.load_file(protocols[protocol]).protocols[protocol]
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


def cohens_d(group1, group2):
    # Calculate means
    m1, m2 = group1.mean(), group2.mean()

    # Calculate variance (using ddof=1 for sample variance)
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)

    # Calculate pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    # Calculate Cohen's d
    return (m1 - m2) / pooled_std


def p_value(group1, group2):
    t, p = scipy.stats.ttest_ind(group1, group2)
    return p


def add_tests(df):
    results = []

    for (protocol, query), group in df.groupby(["protocol", "query"]):
        mambo_data = group[group["method"] == "mambo"]["duration"]

        for method in ["tango", "tango+"]:
            method_data = group[group["method"] == method]["duration"]
            if len(mambo_data) > 0 and len(method_data) > 0:
                d = cohens_d(method_data, mambo_data)
                p = p_value(method_data, mambo_data)
                results.append(
                    {
                        ("protocol", ""): protocol,
                        ("query", ""): query,
                        ("method", ""): method,
                        ("duration", "cohens_d"): d,
                        ("duration", "p_value"): p,
                    }
                )

    df = pd.DataFrame(results)
    return df


@experiment.postprocess
def postprocess(results):
    # ensure data is numeric, in case it was improperly loaded from file
    results = results.apply(pd.to_numeric, errors="ignore")

    # convert duration to milliseconds
    results["duration"] = results["duration"] * 1000

    stats = results.groupby(["protocol", "query", "method", "result"]).agg(
        {"duration": ["mean", "std", "min", "max"]}
    )

    index = stats.index
    duration_stats = stats.reset_index()
    tests_df = add_tests(results.reset_index())

    tuples = tests_df.transpose().index
    new_columns = pd.MultiIndex.from_tuples(tuples)
    tests_df.columns = new_columns
    merged = duration_stats.merge(tests_df, how="left").round(3)
    merged.reindex(index=index)
    print(merged)

    pivot = results.reset_index().pivot_table(
        index=["protocol", "query"],
        columns=["method"],
        values="duration",
        aggfunc="mean",
    )
    print(pivot.round(3))
    print(pivot.to_csv())

    return merged


if __name__ == "__main__":
    # for protocol in protocols:
    #     protocol = bspl.load_file(protocols[protocol]).protocols[protocol]
    #     print(
    #         f"{protocol}\\\\\\small {len(protocol.messages)} messages\\\\{len(protocol.parameters)} parameters\\\\{len(list(tango.max_paths(protocol)))} enactments"
    #     )
    fire.Fire(experiment)
