#!/usr/bin/env python3

import pytest
from bspl.parser import load_file, load
from bspl.generators.asl import *


@pytest.fixture(scope="module")
def Logistics():
    return load_file("samples/logistics2.bspl").protocols["Logistics"]


@pytest.fixture(scope="module")
def Packer(Logistics):
    return Logistics.roles["Packer"]


def test_generate_covers(Logistics, Packer):
    m = Logistics.messages
    assert generate_covers(Logistics, Packer) == {
        m["Packed"]: [{m["Wrapped"], m["Labeled"]}]
    }
    assert generate_covers(Logistics, Logistics.roles["Merchant"]) == {
        m["RequestLabel"]: [set()],
        m["RequestWrapping"]: [{m["RequestLabel"]}],
    }
    assert generate_covers(Logistics, Logistics.roles["Wrapper"]) == {
        m["Wrapped"]: [{m["RequestWrapping"]}]
    }
    assert generate_covers(Logistics, Logistics.roles["Labeler"]) == {
        m["Labeled"]: [{m["RequestLabel"]}]
    }


def test_generate_goals(Logistics, Packer):
    m = Logistics.messages
    r = Logistics.roles
    cs = generate_covers(Logistics, Packer)
    goals = generate_goals(cs)
    print(goals)
    assert (
        """+wrapped(Wrapper, Packer, OrderID, ItemID, Item, Wrapping)\n  : labeled(Labeler, Packer, OrderID, Address, Label)\n  <- !send_packed(OrderID, ItemID, Wrapping, Label).\n"""
        in goals
    )
    assert (
        """+labeled(Labeler, Packer, OrderID, Address, Label)\n  : wrapped(Wrapper, Packer, OrderID, ItemID, Item, Wrapping)\n  <- !send_packed(OrderID, ItemID, Wrapping, Label).\n"""
        in goals
    )
    assert (
        """!send_packed(OrderID, ItemID, Wrapping, Label)\n  <- .emit(packed(Packer, Merchant, OrderID, ItemID, Wrapping, Label, Status)).\n"""
        in goals
    )

    cs = generate_covers(Logistics, r["Merchant"])
    goals = generate_goals(cs)
    assert (
        """!send_request_label\n  <- .emit(request_label(Merchant, Labeler, OrderID, Address)).\n"""
        in goals
    )
    assert (
        """+request_label(Merchant, Labeler, OrderID, Address)\n  <- !send_request_wrapping(OrderID).\n"""
        in goals
    )
    assert (
        """!send_request_wrapping(OrderID)\n  <- .emit(request_wrapping(Merchant, Wrapper, OrderID, ItemID, Item)).\n"""
        in goals
    )


def test_prune(Logistics, Packer):
    covered = load(
        """
Covered {
  roles A, B
  parameters out ID key, out data, result
  private extra, other

  A -> B: start[out ID, out extra]
  A -> B: xfer[in ID, out data, out other]
  B -> A: process[in ID, in data, out result]
}
"""
    ).protocols["Covered"]

    A = covered.roles["A"]
    B = covered.roles["B"]

    m = covered.messages

    B_covers = generate_covers(covered, B)
    assert B_covers == {
        m["process"]: [{m["xfer"], m["start"]}],
    }  # start is a dependency of xfer, so it should be pruned
    B_pruned = {m: [prune(m, c) for c in B_covers[m]] for m in B_covers}
    assert B_pruned == {
        m["process"]: [{m["xfer"]}],
    }


def test_dependent_protocol():
    p = load(
        """
    P {
        roles A, B
        parameters in id key, out done

        A -> B: start[in id, out done]
    }
    """
    ).protocols["P"]
    m = p.messages
    covers = generate_covers(p, p.roles["A"])
    assert not covers[m["start"]] == [{m["start"]}]
