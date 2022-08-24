#!/usr/bin/env python3

import pytest
from bspl.parsers.langshaw import load, load_file
from bspl import langshaw
from bspl.langshaw import *
import inspect
from bspl.verification.paths import liveness, safety

purchase_spec = """
who B, S, Sh
what ID key, item, price, Reject or Deliver

action
  B: RFQ(ID, item)
  S: Quote(ID, item, price)
  B: Accept(ID, item, price, address)
  B: Reject(ID, Quote)
  S: Instruct(ID, Accept, fee)
  Sh: Deliver(ID, item, address, Instruct)

conflict
  Accept Reject
  Reject Deliver

sayso
  B > S: item
  S > B: price
  B > Sh: address
  S: fee

see
  B: Quote, Deliver
  S: RFQ, Accept, Reject, Deliver
  Sh: fee, Instruct
"""


@pytest.fixture(scope="module")
def PurchaseSpec():
    return load(purchase_spec)


@pytest.fixture(scope="module")
def Purchase(PurchaseSpec):
    return Langshaw(PurchaseSpec)


@pytest.fixture(scope="module")
def RFQ(Purchase):
    return Purchase.actions[0]


@pytest.fixture(scope="module")
def Reject(Purchase):
    return Purchase.actions[3]


def test_grammar():
    load("\nwho: A\n")  # extra whitespace
    load("what: A, B, C or D")
    load("actions:\n  A: Act(a,b,c)\n")
    load("actions: A: Act(a,b,c)\n")


def test_load_file():
    assert load_file("samples/tests/langshaw/purchase.lsh")


def test_delegates():
    assert delegates("item->S")
    assert not delegates("item")


def test_validate(PurchaseSpec):
    assert validate(PurchaseSpec)

    with pytest.raises(Exception) as e:
        validate(
            load(
                inspect.cleandoc(
                    """
        who A, B
        what a, b
        actions:
            A: Send(a)
        sayso:
          A > B: a
          B: a
        """
                )
            )
        )
        assert e


def test_langshaw_get_clause(PurchaseSpec):
    who = langshaw.get_clause(PurchaseSpec, "who")
    print(who)
    assert who

    what = langshaw.get_clause(PurchaseSpec, "what")
    print(what)
    assert what

    actions = langshaw.get_clause(PurchaseSpec, "actions")
    print(actions)
    assert actions


def test_langshaw_roles(Purchase):
    assert Purchase.roles == ["B", "S", "Sh"]


def test_langshaw_parameters(Purchase):
    assert Purchase.parameters == [
        "ID",
        "item",
        "price",
        "Reject",
        "Deliver",
    ]


def test_langshaw_private(Purchase):
    assert Purchase.private == set(
        [
            "RFQ",
            "Accept",
            "Quote",
            "Instruct",
            "fee",
            "address",
            "Reject",
            "Deliver",
            "item->S",
            "price->B",
            "address->Sh",
        ]
    )


def test_langshaw_keys(Purchase):
    assert list(Purchase.keys) == ["ID"]


def test_langshaw_actions(Purchase):
    assert len(Purchase.actions) == 6
    assert Purchase.actions[0].actor == "B"
    assert Purchase.actions[0].name == "RFQ"
    assert Purchase.actions[0].parameters == ["ID", "item"]


def test_langshaw_conflicts(Purchase):
    assert len(Purchase.conflicts) == 2
    assert len(Purchase.conflicts[0]) == 2
    assert Purchase.conflicts[0] == ["Accept", "Reject"]


def test_langshaw_can_bind(Purchase):
    assert Purchase.can_bind("B", "item")
    assert Purchase.can_bind("S", "item")
    assert Purchase.can_bind("B", "RFQ")
    assert not Purchase.can_bind("S", "RFQ")
    assert not Purchase.can_bind("Sh", "item")


def test_langshaw_can_be_delegated(Purchase):
    assert Purchase.can_be_delegated("S", "item")
    assert not Purchase.can_be_delegated("B", "item")
    assert not Purchase.can_be_delegated("B", "nonexistent-parameter")


def test_langshaw_delegates_to(Purchase):
    assert Purchase.delegates_to("B", "item") == "S"
    assert Purchase.delegates_to("S", "item") == None
    assert Purchase.delegates_to("Sh", "item") == None


def test_action_delegations(Purchase):
    assert list(Purchase.actions[0].delegations) == ["item->S"]
    assert list(Purchase.actions[1].delegations) == ["item->S", "price->B"]


def test_action_expanded_parameters(Purchase):
    assert list(Purchase.actions[0].expanded_parameters) == ["item->S", "item"]
    assert list(Purchase.actions[1].expanded_parameters) == [
        "item->S",
        "item",
        "price->B",
        "price",
    ]


def test_action_possibilities(RFQ, Reject):
    assert RFQ.possibilities("ID") == ["in", "out"]
    assert RFQ.possibilities("item") == ["in", "out", "nil"]
    assert Reject.possibilities("ID") == ["in", "out"]
    assert Reject.possibilities("Quote") == ["in"]


def test_langshaw_can_see(Purchase):
    assert Purchase.can_see("B", "item")
    assert Purchase.can_see("S", "item")
    assert not Purchase.can_see("Sh", "price")


def test_langshaw_capabilities(Purchase):
    assert Purchase.capabilities("B", "ID") == {"in", "out"}
    assert Purchase.capabilities("B", "item") == {"out", "delegate"}


def test_action_all_schemas(Purchase):
    result = list(Purchase.actions[0].all_schemas())
    print(result)
    assert result == [
        (("ID", "in"), ("item->S", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "in"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "in"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "out"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "out"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "nil"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "in"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "in"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "out"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "out"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "nil"), ("item", "nil"), ("RFQ", "out")),
    ]


def test_delegation_role_alignment():
    f = delegation_role_alignment("B")
    assert f((("ID", "in"), ("item->S", "nil"), ("item", "nil")))
    assert not f((("ID", "in"), ("item->S", "in"), ("item", "nil")))
    assert f((("ID", "in"), ("item->B", "in"), ("item", "nil")))
    assert f((("ID", "in"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")))


def test_delegation_out_parameter_nil():
    f = delegation_out_parameter_nil
    assert f((("item", "out"), ("item->S", "in")))
    assert f((("item", "nil"), ("item->S", "out")))
    assert not f((("item", "out"), ("item->S", "out")))
    assert not f((("item", "in"), ("item->S", "out")))
    assert f((("ID", "in"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")))


def test_ensure_sayso():
    f = ensure_sayso
    assert f((("item", "out"), ("item->S", "in")))
    assert f((("item", "nil"), ("item->S", "in"), ("item->Sh", "out")))
    assert f((("item", "nil"), ("item->S", "out")))
    assert f((("ID", "in"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")))
    assert not f((("item", "nil"), ("item->S", "nil")))


def test_out_keys():
    f = out_keys(["ID"])
    assert f((("ID", "out"), ("item", "out")))
    assert not f((("ID", "out"), ("item", "in")))
    assert f((("ID", "in"), ("item", "in")))
    assert f((("ID", "in"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")))


def test_action_schemas(Purchase):
    result = list(Purchase.actions[0].schemas())  # RFQ
    print(result)
    assert result == [
        # can't have in for delegation to other role
        # (("ID", "in"), ("item->S", "in"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "in"), ("item->S", "in"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "in"), ("item->S", "in"), ("item", "nil"), ("RFQ", "out")),
        # if delegation is out, parameter must be nil
        # (("ID", "in"), ("item->S", "out"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "in"), ("item->S", "out"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "out"), ("item->S", "out"), ("item", "out"), ("RFQ", "out")),
        # parameter and delegations cannot all be nil
        # (("ID", "in"), ("item->S", "nil"), ("item", "nil"), ("RFQ", "out")),
        # (("ID", "out"), ("item->S", "nil"), ("item", "nil"), ("RFQ", "out")),
        # can't have out keys with in parameters
        # (("ID", "out"), ("item->S", "in"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "out"), ("item->S", "in"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "out"), ("item->S", "in"), ("item", "nil"), ("RFQ", "out")),
        # (("ID", "out"), ("item->S", "out"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "out"), ("item->S", "nil"), ("item", "in"), ("RFQ", "out")),
        # ok
        (("ID", "in"), ("item->S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item->S", "nil"), ("item", "out"), ("RFQ", "out")),
    ]


def test_langshaw_extend_schemas(Purchase):
    assert list(Purchase.extend_schemas(Purchase.actions[3]))


def test_langshaw_alt_parameters(Purchase):
    print(Purchase.alt_parameters)
    assert False


def test_langshaw_recipients(Purchase, RFQ):
    result = list(Purchase.recipients(RFQ, s) for s in RFQ.schemas())
    assert result


def test_langshaw_messages(Purchase, RFQ):
    ms = Purchase.messages(RFQ)
    print("\n".join(m.format() for m in ms))
    assert False


def test_langshaw_completion_messages(Purchase):
    result = Purchase.completion_messages()
    print("\n".join(m.format() for m in result))
    assert result


def test_langshaw_to_bspl(Purchase):
    p = Purchase.to_bspl("Purchase")
    print(p.format())
    assert False


def test_liveness(Purchase):
    p = Purchase.to_bspl("Purchase")
    assert liveness(p)
