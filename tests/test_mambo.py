#!/usr/bin/env python3

import pytest
import math
from bspl.parsers import precedence, bspl
from bspl.verification.paths import max_paths, UoD
from bspl.verification.mambo import *


@pytest.fixture(scope="module")
def CreateOrder():
    return bspl.load_file("samples/merged-lab-order.bspl").protocols["CreateOrder"]


@pytest.fixture(scope="module")
def Purchase():
    return bspl.load_file("samples/tests/po-pay-cancel-ship.bspl").protocols[
        "PO Pay Cancel Ship"
    ]


@pytest.fixture(scope="module")
def NetBill():
    return bspl.load_file("samples/netbill.bspl").protocols["NetBill"]


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
