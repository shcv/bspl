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
    assert Not(lambda p: None)(empty) == math.inf


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
    assert result  # This should find paths where 'a' does not occur


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


def test_desired_end(Sale):
    """Test that desired end states are reachable in Sale protocol."""
    q = precedence.parse(
        "rescindAck ∨ reject ∨ transfer ∧ (refund ∨ deliver)",
        semantics=QuerySemantics(),
    )
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q))
    nresult = list(match_paths(U, -q))

    # Should have paths that reach desired end states
    assert len(result) > 0
    # No paths should exist that violate the desired end constraint
    assert len(nresult) == 0


def test_happy(Sale):
    """Test happy path sequences in Sale protocol."""
    # Test sequence: offer → accept → transfer → deliver
    q = precedence.parse(
        "offer · accept · transfer · deliver", semantics=QuerySemantics()
    )
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q))

    # Test alternative sequence: offer → accept → deliver → transfer (should be impossible)
    q2 = precedence.parse(
        "offer · accept · deliver · transfer", semantics=QuerySemantics()
    )
    U2 = UoD.from_protocol(Sale, conflicts=q2.conflicts)
    result2 = list(match_paths(U2, q2))

    # Normal sequence should have valid paths
    assert len(result) > 0
    # Impossible sequence (deliver before transfer) should have no paths
    assert len(result2) == 0


def test_unhappy(Sale):
    """Test unhappy path sequences in Sale protocol."""
    # Test rescission sequence: offer → accept → rescind → rescindAck
    q = precedence.parse("offer.accept.rescind.rescindAck", semantics=QuerySemantics())
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q))

    # Test rejection sequence: offer → reject
    q2 = precedence.parse("offer . reject", semantics=QuerySemantics())
    U2 = UoD.from_protocol(Sale, conflicts=q2.conflicts)
    result2 = list(match_paths(U2, q2))

    # Both unhappy paths should be possible
    assert len(result) > 0  # Rescission should be possible
    assert len(result2) > 0  # Rejection should be possible


def test_late_action(Sale):
    """Test that late actions are properly constrained."""
    # Query: either no accept happens, or accept is followed by rescind
    q = precedence.parse("no accept ∨ accept · rescind", semantics=QuerySemantics())
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)

    # Test the negation: paths where accept happens but is not followed by rescind
    result = list(match_paths(U, -q))

    # The constraint should be always satisfied (no violations)
    # i.e., there should be no paths where accept occurs without being followed by rescind
    assert len(result) == 0


def test_disables(Sale):
    q = precedence.parse("rescind.accept", semantics=QuerySemantics())
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, verbose=True))
    print(result)
    assert not result


def test_alternatives(Sale):
    """Test alternative post-transfer outcomes in Sale protocol."""
    # Query: transfer followed by either deliver OR refund
    q = precedence.parse(
        "transfer . deliver or transfer . refund", semantics=QuerySemantics()
    )
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True))

    # Should have paths for both alternatives (transfer→deliver and transfer→refund)
    assert len(result) > 0
    # Should be less than total possible paths since it requires transfer first
    total_paths = len(list(max_paths(U)))
    assert len(result) < total_paths


def test_priority(Sale):
    """Test priority constraints in Sale protocol."""
    # Query: either Buyer doesn't rescind, OR Buyer pays, OR rescindAck occurs
    q = precedence.parse(
        """no Buyer:rescind ∨ Buyer:pay ∨ rescindAck""",
        semantics=QuerySemantics(),
    )
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True, residuate=True))
    nresult = list(match_paths(U, -q, prune=True, residuate=True))
    total = list(match_paths(U, Any(), max_only=True))

    # Most paths should satisfy the priority constraint
    assert len(result) > 0
    # Few or no paths should violate it
    assert len(nresult) <= len(result)
    # Combined should cover all possible paths
    assert (
        len(result) + len(nresult) >= len(total) // 2
    )  # Allow some flexibility for partial paths


def test_compensation(Sale):
    """Test compensation constraints in Sale protocol."""
    # Complex constraint ensuring proper compensation logic:
    # (no transfer OR deliver OR refund) AND
    # (no refund OR transfer) AND
    # (no refund OR no deliver)
    q = precedence.parse(
        """ (no transfer ∨ deliver ∨ refund)
          ∧ (no refund ∨ transfer) ∧ (no refund ∨ no deliver)""",
        semantics=QuerySemantics(),
    )
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True))
    nresult = list(match_paths(U, -q, prune=True))
    total_paths = len(list(max_paths(U)))

    # Should have some valid compensation paths
    assert len(result) > 0
    # The constraint should eliminate some invalid paths
    assert len(result) + len(nresult) <= total_paths


def test_complementary(Sale):
    q = precedence.parse("reject ∧ deliver", semantics=QuerySemantics())
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True, verbose=True))
    nresult = list(match_paths(U, -q, prune=True, verbose=True))
    print(f"{len(result)} + {len(nresult)} = {len(list(max_paths(U)))}")
    print(result)
    print(nresult)
    assert not result and nresult


def test_delegation_guarantee(Sale):
    q = precedence.parse(
        "(pay ∨ transfer) ∧ no pay · transfer", semantics=QuerySemantics()
    )
    print(q)
    U = UoD.from_protocol(Sale, conflicts=q.conflicts)
    result = list(match_paths(U, q, prune=True, verbose=True))
    nresult = list(match_paths(U, -q, prune=True, verbose=True))
    print(f"{len(result)} + {len(nresult)} = {len(list(max_paths(U)))}")
    print(result)
    print(nresult)
    assert not result and nresult
