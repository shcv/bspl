#!/usr/bin/env python3

import pytest
import math
import glob
import os
from statistics import mean, stdev
import pandas as pd
from ttictoc import Timer
from itertools import product
from bspl.parsers import precedence, bspl
from bspl.verification.paths import UoD, live, safe, max_paths
from bspl.verification.mambo import *
from bspl.generators.mambo import unsafe, nonlive


@pytest.fixture(scope="module")
def CreateOrder():
    return bspl.load_file("samples/merged-lab-order.bspl").protocols["CreateOrder"]


@pytest.fixture(scope="module")
def Purchase():
    return bspl.load_file("samples/purchase.bspl").protocols["Purchase"]


@pytest.fixture(scope="module")
def NetBill():
    return bspl.load_file("samples/netbill.bspl").protocols["NetBill"]


@pytest.fixture(scope="module")
def Ebusiness():
    return bspl.load_file("samples/ebusiness.bspl").protocols["Ebusiness"]


@pytest.fixture(scope="module")
def Sale():
    return bspl.load_file("samples/sale.bspl").protocols["Sale"]


def test_occurs(NetBill):
    p = "price"
    q = Occurs(p)
    for path in match_paths(UoD.from_protocol(NetBill), q):
        assert q(path) == 2


empty = Path.create_empty()


def test_or():
    # returns min of results from branches
    assert Or(lambda p: 1, lambda p: 2)(empty) == 1
    assert Or(lambda p: 1, lambda p: None)(empty) == 1
    assert Or(lambda p: None, lambda p: 2)(empty) == 2
    assert Or(lambda p: False, lambda p: 2)(empty) == 2
    assert Or(lambda p: False, lambda p: None)(empty) == None
    assert Or(lambda p: False, lambda p: False)(empty) == False


def test_and():
    assert And(lambda p: 1, lambda p: 2)(Path.create_empty()) == 2
    assert And(lambda p: 0, lambda p: 2)(Path.create_empty()) == 2
    assert And(lambda p: 1, lambda p: None)(Path.create_empty()) == None
    assert And(lambda p: None, lambda p: 2)(Path.create_empty()) == None
    assert And(lambda p: None, lambda p: 0)(Path.create_empty()) == None
    assert And(lambda p: False, lambda p: 2)(Path.create_empty()) == False
    assert And(lambda p: 2, lambda p: False)(Path.create_empty()) == False
    assert And(lambda p: 0, lambda p: False)(Path.create_empty()) == False


def test_not():
    assert Not(lambda p: 1)(empty) == False
    assert Not(lambda p: False)(empty) == math.inf
    assert Not(lambda p: None)(empty) == None


def test_before():
    assert Before(lambda p: 1, lambda p: 2)(empty) == 2
    assert Before(lambda p: 2, lambda p: 1)(empty) == False
    assert Before(lambda p: 2, lambda p: None)(empty) == None
    assert Before(lambda p: None, lambda p: 2)(empty) == None


def test_conflicts(NetBill):
    query = "C:item . M:price & item . payment | ( confirmation . document | document . payment )"
    q = precedence.parse(query, semantics=QuerySemantics())
    print(q.conflicts)


def test_tangles(Ebusiness):
    query = "price . decision"
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Ebusiness, conflicts=q.conflicts)
    print(q.conflicts)
    print(U.tangle.tangles)
    print(len(list(match_paths(U, q))))

    query = "decision . details"
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Ebusiness, conflicts=q.conflicts)
    print(q.conflicts)
    print(U.tangle.tangles)
    print(len(list(match_paths(U, q))))

    query = (
        "decision . details & decision . payment & decision . status & payment . status"
    )
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Ebusiness, conflicts=q.conflicts)
    print(q.conflicts)
    print(U.tangle.tangles)
    print(len(list(match_paths(U, q))))


def test_english(Purchase):
    query = "-ID or -item or -price or -outcome"
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Purchase, conflicts=q.conflicts)
    count = 0

    t = Timer()
    t.start()
    for p in match_paths(U, q):
        count += 1
    print(count, t.stop())
    print(len(list(max_paths(U))))
    print(live(Purchase))
    # assert False


def test_memoization(Ebusiness):
    query = (
        "details . decision & decision . payment & decision . status & payment . status"
    )
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Ebusiness, conflicts=q.conflicts)

    t = Timer()
    t.start()
    result = None
    for i in range(1):
        result = list(match_paths(U, q))
    print(t.stop())

    print(len(result))
    # assert False


def test_enactable():
    P = bspl.load_file("samples/tests/enactable01").protocols["Enactable1"]
    q = precedence.parse("not a", semantics=QuerySemantics())
    U = UoD.from_protocol(P)
    result = list(match_paths(U, q))
    assert result

    P = bspl.load_file("samples/tests/nonlive-dependent").protocols["Dependent"]
    q = precedence.parse("not a", semantics=QuerySemantics())
    U = UoD.from_protocol(P, external=False)
    result = list(match_paths(U, q))
    assert not result


def test_liveness(Ebusiness):
    # q = nonlive(Ebusiness)
    # U = UoD.from_protocol(Ebusiness, conflicts=q.conflicts)
    # print(q)
    # result = list(match_paths(U, q))
    # print(result)
    # assert not result

    # P = bspl.load_file("samples/tests/nonlive-dependent").protocols["Dependent"]
    # q = nonlive(P)
    # U = UoD.from_protocol(P, conflicts=q.conflicts, external=False)
    # print(q)
    # result = list(match_paths(U, q))
    # print(result)
    # assert result

    P = bspl.load_file("samples/tests/nonlive-indirect").protocols["IndirectNonlive"]
    q = nonlive(P)
    U = UoD.from_protocol(P, conflicts=q.conflicts)
    print(q)
    result = next(match_paths(U, q), None)
    print(result)
    assert result


def test_safety(Ebusiness, Purchase):
    q = unsafe(Ebusiness)
    assert not q

    t = Timer()
    t.start()
    q = unsafe(Purchase)
    U = UoD.from_protocol(Purchase, conflicts=q.conflicts)
    print(q)
    result = list(match_paths(U, q))
    print(t.stop())
    print(safe(Purchase))
    assert not result
    # assert False


def test_happy_path(Sale):
    q = precedence.parse(
        "offer.accept.pay.transfer.ship.deliver", semantics=QuerySemantics()
    )
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, verbose=True))
    print(result)
    assert result


def test_unhappy_path(Sale):
    q = precedence.parse("offer.accept.rescind.rescindAck", semantics=QuerySemantics())
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, verbose=True))
    print(result)
    assert result


def test_disables(Sale):
    q = precedence.parse("rescind.accept", semantics=QuerySemantics())
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, verbose=True))
    print(result)
    assert not result


def test_alternatives(Sale):
    q = precedence.parse(
        "transfer . deliver or transfer . refund", semantics=QuerySemantics()
    )
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True, verbose=True))
    print(f"{len(result)} : {len(list(max_paths(U)))}")
    print(result)
    assert False


def test_compensation(Sale):
    q = precedence.parse(
        """ (no transfer ∨ deliver ∨ refund)
          ∧ (no refund ∨ transfer) ∧ (no refund ∨ no deliver)""",
        # """transfer and no (deliver or refund)""",
        semantics=QuerySemantics(),
    )
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True, verbose=True))
    nresult = list(match_paths(U, -q, prune=True, verbose=True))
    print(f"{len(result)} + {len(nresult)} = {len(list(max_paths(U)))}")
    print(result)
    print(nresult)
    assert False


def test_priority(Sale):
    q = precedence.parse(
        """no rescind ∨ pay ∨ rescindAck""",
        semantics=QuerySemantics(),
    )
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True, residuate=True, verbose=True))
    print(result)
    nresult = list(match_paths(U, -q, prune=True, residuate=True, verbose=True))
    print(nresult)
    total = len(list(max_paths(U)))
    print(f"{len(result)} + {len(nresult)} = {total}")
    assert len(result) + len(nresult) == total
    assert False


def format_table(columns, data):
    # calculate max size of each column for padding
    sizes = {c: max(len(c), max(len(str(row[c])) for row in data)) for c in columns}

    def justify(column, value):
        return str(value).ljust(sizes[column], " ")

    # header
    result = [" & ".join(justify(c, c) for c in columns) + " \\\\ " + "\\hline"]

    for entry in data:
        result.append(
            " & ".join(justify(c, entry.get(c, "")) for c in columns) + " \\\\"
        )

    return "\n".join(result)


def test_safety_performance():
    files = glob.glob("samples/*.bspl")
    columns = [
        "File",
        "Protocol",
        "Formula",
        "Result",
        "Time",
    ]

    stats = []
    for f in files:
        spec = bspl.load_file(f)
        for name, P in spec.protocols.items():
            t = Timer()
            t.start()
            q = unsafe(P)
            if q:
                U = UoD.from_protocol(P, conflicts=q.conflicts)
                result = next(match_paths(U, q), None)
            else:
                result = []
            elapsed = t.stop()
            stats.append(
                {
                    "File": os.path.basename(f),
                    "Protocol": name,
                    "Formula": str(q),
                    "Result": not result,
                    "Time": elapsed,
                }
            )
    print(format_table(columns, stats))


def test_liveness_performance():
    files = glob.glob("samples/*.bspl")
    columns = [
        "Protocol",
        "Result",
        "Live",
        "Time",
        "Opt"
        # "Base",
        # "Prune",
        # "Residuate",
        # "Both",
    ]

    configurations = {
        "Base": {"residuate": False, "prune": False},
        "Prune": {"residuate": False, "prune": True},
        "Residuate": {"residuate": True, "prune": False},
        "Both": {"residuate": True, "prune": True},
    }

    stats = []
    for f in files:
        spec = bspl.load_file(f)
        for name, P in spec.protocols.items():
            for label, config in configurations.items():
                t = Timer()
                t.start()
                q = nonlive(P)
                if q:
                    U = UoD.from_protocol(P, conflicts=q.conflicts)
                    result = next(match_paths(U, q, **config), None)
                else:
                    result = []
                elapsed = t.stop()
                print(name, label, 1000 * elapsed, 1000 * live(P)["elapsed"])
                # stats.append(
                #     {
                #         "File": os.path.basename(f),
                #         "Protocol": name,
                #         "Formula": str(q),
                #         "Result": result,
                #         "Opt": label,
                #         "Live": live(P),
                #         "Time": elapsed,
                #     }
                # )
    # print(format_table(columns, stats))
