#!/usr/bin/env python3

import pytest
from bspl.parsers.bspl import load_file, load
from bspl.generators.asl import *


@pytest.fixture(scope="module")
def Logistics():
    return load_file("samples/logistics/logistics2.bspl").protocols["Logistics"]


@pytest.fixture(scope="module")
def Packer(Logistics):
    return Logistics.roles["Packer"]


@pytest.fixture(scope="module")
def ConflictProtocol():
    return load(
        """
Protocol {
  roles A, B
  parameters out id key, out result
  private x, y

  A -> B: First[out id, out x]
  A -> B: Second[out id, out y]
  B -> A: Response[in id, in x, out result]
  B -> A: Alternative[in id, out result]
}
    """
    ).protocols["Protocol"]


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
    assert (
        """+wrapped(MasID, Wrapper, Packer, OrderID, ItemID, Item, Wrapping)\n  : labeled(MasID, Labeler, Packer, OrderID, Address, Label)\n  <- !send_packed(MasID, Packer, Merchant, OrderID, ItemID, Wrapping, Label).\n"""
        in goals
    )
    assert (
        """+labeled(MasID, Labeler, Packer, OrderID, Address, Label)\n  : wrapped(MasID, Wrapper, Packer, OrderID, ItemID, Item, Wrapping)\n  <- !send_packed(MasID, Packer, Merchant, OrderID, ItemID, Wrapping, Label).\n"""
        in goals
    )
    assert (
        """+!send_packed(MasID, Packer, Merchant, OrderID, ItemID, Wrapping, Label)\n  <- // insert code to compute Packed out parameters ['status'] here\n     .emit(packed(MasID, Packer, Merchant, OrderID, ItemID, Wrapping, Label, Status)).\n"""
        in goals
    )

    cs = generate_covers(Logistics, r["Merchant"])
    goals = generate_goals(cs)
    print(goals)
    assert (
        """+!send_request_label\n  <- // insert code to compute RequestLabel out parameters ['address', 'orderID'] here\n     .emit(request_label(MasID, Merchant, Labeler, OrderID, Address)).\n"""
        in goals
    )
    assert (
        """+request_label(MasID, Merchant, Labeler, OrderID, Address)\n  <- // insert code to compute RequestWrapping out parameters ['item', 'itemID'] here\n     .emit(request_wrapping(MasID, Merchant, Wrapper, OrderID, ItemID, Item)).\n"""
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


def test_identify_conflicts(ConflictProtocol):
    """Test identification of conflicting messages"""
    A = ConflictProtocol.roles["A"]
    B = ConflictProtocol.roles["B"]

    # Test from role A's perspective
    response = ConflictProtocol.messages["Response"]
    alternative = ConflictProtocol.messages["Alternative"]

    # Alternative and Response both have 'result' as out, so they conflict
    conflicts = identify_conflicts(ConflictProtocol, B)
    assert response in conflicts[alternative]
    assert alternative in conflicts[response]

    # Test from role B's perspective
    first = ConflictProtocol.messages["First"]
    second = ConflictProtocol.messages["Second"]

    # First and Second both have 'id' as out, so they conflict
    conflicts = identify_conflicts(ConflictProtocol, A)
    assert first in conflicts[second]


def test_generate_goals_with_conflicts(ConflictProtocol):
    """Test goal generation with conflict guards for messages that conflict"""
    B = ConflictProtocol.roles["B"]

    response = ConflictProtocol.messages["Response"]
    alternative = ConflictProtocol.messages["Alternative"]

    # Generate covers for B's emissions
    covers = generate_covers(ConflictProtocol, B)
    conflicts = identify_conflicts(ConflictProtocol, B)

    # Generate goals with conflict guards
    goals = generate_goals(covers, conflicts)

    print(goals)

    # Check that Alternative has a guard to block if Response exists
    alternative_goal = None
    for goal in goals:
        if ".emit(alternative" in goal:
            alternative_goal = goal
            break

    assert alternative_goal is not None
    # The plan should include a guard like "not response(...)"
    assert "not response" in alternative_goal

    # Similarly, check that Response has a guard to block if Alternative exists
    response_goal = None
    for goal in goals:
        if ".emit(response" in goal:
            response_goal = goal
            break

    assert response_goal is not None
    # The plan should include a guard like "not alternative(...)"
    assert "not alternative" in response_goal
