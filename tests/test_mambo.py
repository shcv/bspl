#!/usr/bin/env python3

import pytest
import math
from bspl.parsers import precedence, bspl
from bspl.verification.paths import max_paths, UoD, live
from bspl.verification.mambo import *


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


def test_find(NetBill):
    ps = [("item", 0), ("price", 2)]
    for path in max_paths(UoD.from_protocol(NetBill)):
        for p, i in ps:
            assert find(path, p) == i


def test_find_role(NetBill):
    p = "M:item"
    for path in max_paths(UoD.from_protocol(NetBill)):
        assert find(path, p) == 1


def test_occurs(NetBill):
    p = "price"
    q = occurs(p)
    for path in max_paths(UoD.from_protocol(NetBill)):
        assert q(path) == 2


def test_or():
    # returns min of results from branches
    assert Or(lambda p: 1, lambda p: 2)() == 1
    assert Or(lambda p: 1, lambda p: None)() == 1
    assert Or(lambda p: None, lambda p: 2)() == 2


def test_and():
    assert And(lambda p: 1, lambda p: 2)() == 2
    assert And(lambda p: 1, lambda p: None)() == None
    assert And(lambda p: None, lambda p: 2)() == None


def test_not():
    assert Not(lambda p: 1)() == None
    assert Not(lambda p: None)() == math.inf


def test_before():
    assert before(lambda p: 1, lambda p: 2)() == True
    assert before(lambda p: 2, lambda p: 1)() == False
    assert before(lambda p: 2, lambda p: None)() == None
    assert before(lambda p: None, lambda p: 2)() == None


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
    print(len(list(max_paths(U))))

    query = "decision . details"
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Ebusiness, conflicts=q.conflicts)
    print(q.conflicts)
    print(U.tangle.tangles)
    print(len(list(max_paths(U))))

    query = (
        "decision . details & decision . payment & decision . status & payment . status"
    )
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Ebusiness, conflicts=q.conflicts)
    print(q.conflicts)
    print(U.tangle.tangles)
    print(len(list(max_paths(U))))


def test_english(Purchase):
    query = "-ID or -item or -price or -outcome"
    q = precedence.parse(query, semantics=QuerySemantics())
    U = UoD.from_protocol(Purchase, conflicts=q.conflicts)
    count = 0
    from ttictoc import Timer

    t = Timer()
    t.start()
    for p in max_paths(U, query=q):
        count += 1
    print(count, t.stop())
    print(len(list(max_paths(U))))
    print(live(Purchase))
    assert False
