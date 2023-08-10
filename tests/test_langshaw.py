#!/usr/bin/env python3

import pytest
from bspl.parsers.langshaw import load, load_file
from bspl import langshaw
from bspl.langshaw import *
import inspect
from bspl.verification.paths import liveness, safety
import pprint


@pytest.fixture(scope="module")
def PurchaseSpec():
    return load_file("samples/tests/langshaw/purchase.lsh")


@pytest.fixture(scope="module")
def Purchase():
    return Langshaw(load_file("samples/tests/langshaw/purchase.lsh"))


@pytest.fixture(scope="module")
def Nonlive():
    return Langshaw(load_file("samples/tests/langshaw/nonlive.lsh"))


@pytest.fixture(scope="module")
def BlockContra():
    return Langshaw(load_file("samples/tests/langshaw/block-contra.lsh"))


@pytest.fixture(scope="module")
def EitherOffer():
    return Langshaw(load_file("samples/tests/langshaw/either-offer.lsh"))


@pytest.fixture(scope="module")
def Redelegation():
    return Langshaw(load_file("samples/tests/langshaw/redelegation.lsh"))


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
    assert delegates("item@S")
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
        "Reject",
        "Deliver",
    ]


def test_langshaw_private(Purchase):
    assert Purchase.private == set(
        [
            "item",
            "price",
            "RFQ",
            "Accept",
            "Quote",
            "Instruct",
            "fee",
            "address",
            "Reject",
            "Deliver",
            "item@S",
            "price@B",
            "address@Sh",
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
    assert list(Purchase.actions[0].delegations) == ["item@S"]
    assert list(Purchase.actions[1].delegations) == ["item@S", "price@B"]


def test_action_expanded_parameters(Purchase):
    assert list(Purchase.actions[0].expanded_parameters) == [
        "ID",
        "item@S",
        "item",
        "RFQ",
    ]
    assert list(Purchase.actions[1].expanded_parameters) == [
        "ID",
        "item@S",
        "item",
        "price@B",
        "price",
        "Quote",
    ]


def test_action_possibilities(RFQ, Reject):
    assert RFQ.possibilities("ID") == ["in", "out"]
    assert RFQ.possibilities("item") == ["in", "out", "nil"]
    assert Reject.possibilities("ID") == ["in", "out"]
    assert Reject.possibilities("Quote") == ["in"]


def test_langshaw_observes(Purchase):
    assert Purchase.observes("B", "item")
    assert Purchase.observes("S", "item")
    assert not Purchase.observes("Sh", "price")


def test_langshaw_can_see(Purchase):
    a = {a.name: a for a in Purchase.actions}
    assert Purchase.can_see("B", a["RFQ"])
    assert Purchase.can_see("B", a["Quote"])
    assert Purchase.can_see("S", a["RFQ"])
    # assert not Purchase.can_see("Sh", a["Accept"])


def test_langshaw_recipients(Purchase):
    a = Purchase.actions
    assert Purchase.recipients(a[0]) == {"S"}  # RFQ
    assert Purchase.recipients(a[1]) == {"B"}  # Quote
    # assert Purchase.recipients(a[2]) == {"S", "Sh"}  # Accept


def test_action_all_schemas(Purchase):
    result = list(Purchase.actions[0].all_schemas())
    print(result)
    assert result == [
        (("ID", "in"), ("item@S", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "in"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "in"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "out"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "out"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "nil"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "in"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "in"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "out"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "out"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "nil"), ("item", "nil"), ("RFQ", "out")),
    ]


def test_delegation_role_alignment():
    f = delegation_role_alignment("B")
    assert f((("ID", "in"), ("item@S", "nil"), ("item", "nil")))
    assert not f((("ID", "in"), ("item@S", "in"), ("item", "nil")))
    assert f((("ID", "in"), ("item@B", "in"), ("item", "nil")))
    assert f((("ID", "in"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")))


def test_delegation_out_parameter_nil():
    f = delegation_out_parameter_nil
    assert f((("item", "out"), ("item@S", "in")))
    assert f((("item", "nil"), ("item@S", "out")))
    assert not f((("item", "out"), ("item@S", "out")))
    assert not f((("item", "in"), ("item@S", "out")))
    assert f((("ID", "in"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")))


def test_ensure_sayso():
    f = ensure_sayso
    assert f((("item", "out"), ("item@S", "in")))
    assert f((("item", "nil"), ("item@S", "in"), ("item@Sh", "out")))
    assert f((("item", "nil"), ("item@S", "out")))
    assert f((("ID", "in"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")))
    assert not f((("item", "nil"), ("item@S", "nil")))


def test_ensure_priority(Redelegation):
    f = ensure_priority(Redelegation, "B")

    assert f(
        (  # can bind if received delegation
            ("ID", "in"),
            ("potato@B", "in"),
            ("potato@C", "nil"),
            ("potato", "out"),
            ("Pass", "out"),
        )
    )
    assert f(
        (  # can redelegate if received delegation
            ("ID", "in"),
            ("potato@B", "in"),
            ("potato@C", "out"),
            ("potato", "nil"),
            ("Pass", "out"),
        )
    )
    assert not f(
        (  # can't re-delegate without receiving delegation
            ("ID", "out"),
            ("potato@B", "nil"),
            ("potato@C", "out"),
            ("potato", "nil"),
            ("Pass", "out"),
        )
    )


def test_out_keys():
    f = out_keys(["ID"])
    assert f((("ID", "out"), ("item", "out")))
    assert not f((("ID", "out"), ("item", "in")))
    assert f((("ID", "in"), ("item", "in")))
    assert f((("ID", "in"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")))


def test_RFQ_action_schemas(Purchase):
    result = list(Purchase.actions[0].schemas())  # RFQ
    print(result)
    assert result == [
        # can't have in for delegation to other role
        # (("ID", "in"), ("item@S", "in"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "in"), ("item@S", "in"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "in"), ("item@S", "in"), ("item", "nil"), ("RFQ", "out")),
        # if delegation is out, parameter must be nil
        # (("ID", "in"), ("item@S", "out"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "in"), ("item@S", "out"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "out"), ("item@S", "out"), ("item", "out"), ("RFQ", "out")),
        # parameter and delegations cannot all be nil
        # (("ID", "in"), ("item@S", "nil"), ("item", "nil"), ("RFQ", "out")),
        # (("ID", "out"), ("item@S", "nil"), ("item", "nil"), ("RFQ", "out")),
        # can't have out keys with in parameters
        # (("ID", "out"), ("item@S", "in"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "out"), ("item@S", "in"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "out"), ("item@S", "in"), ("item", "nil"), ("RFQ", "out")),
        # (("ID", "out"), ("item@S", "out"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "out"), ("item@S", "nil"), ("item", "in"), ("RFQ", "out")),
        # ok
        (("ID", "in"), ("item@S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")),
    ]


def test_Quote_action_schemas(Purchase):
    result = list(Purchase.actions[1].schemas())  # RFQ
    print(result)
    assert (  # can bind item if delegated, and delegate price
        ("ID", "in"),
        ("item@S", "in"),
        ("item", "out"),
        ("price@B", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) in result

    # ( # unnecessary case; doesn't make sense for price to be in here
    #     ("ID", "in"),
    #         ("item@S", "in"),
    #         ("item", "out"),
    #         ("price@B", "nil"),
    #         ("price", "in"),
    #         ("Quote", "out"),
    # )

    assert (  # can bind item if delegated, and price
        ("ID", "in"),
        ("item@S", "in"),
        ("item", "out"),
        ("price@B", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) in result

    assert (  # ok; receives bound item, delegates price
        ("ID", "in"),
        ("item@S", "nil"),
        ("item", "in"),
        ("price@B", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) in result

    # assert (  # not ideal; has priority for price but receives it as in without delegating
    #           # in theory, could receive price from one of the agent's other messages
    #     ("ID", "in"),
    #     ("item@S", "nil"),
    #     ("item", "in"),
    #     ("price@B", "nil"),
    #     ("price", "in"),
    #     ("Quote", "out"),
    # ) not in result

    assert (  # ok, receives item, binds price
        ("ID", "in"),
        ("item@S", "nil"),
        ("item", "in"),
        ("price@B", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) in result

    assert (  # not ok; can't bind item without receiving delegation
        ("ID", "in"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "in"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "nil"),
        ("price", "in"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "in"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "out"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "out"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) not in result


def test_redelegation(Redelegation):
    protocol = """
who A, B, C
what ID key, potato

do
  A: Start(ID, potato)
  B: Pass(ID, potato)
  C: Finish(ID, potato)

sayso
  A > B > C: potato
"""
    result = list(Redelegation.actions[1].schemas())  # Pass
    # print(result)
    assert (  # can't receive delegation and parameter in
        ("ID", "in"),
        ("potato@B", "in"),
        ("potato@C", "nil"),
        ("potato", "in"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't receive delegation without binding parameter or delegating
        ("ID", "in"),
        ("potato@B", "in"),
        ("potato@C", "nil"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self; can't have two delegations out
        ("ID", "in"),
        ("potato@B", "out"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self
        ("ID", "in"),
        ("potato@B", "out"),
        ("potato@C", "nil"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self
        ("ID", "out"),
        ("potato@B", "out"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self
        ("ID", "out"),
        ("potato@B", "out"),
        ("potato@C", "nil"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result

    assert (  # can't re-delegate without receiving delegation
        ("ID", "out"),
        ("potato@B", "nil"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result

    assert (  # if ID is in, should have been delegated or bound...
        ("ID", "in"),
        ("potato@B", "nil"),
        ("potato@C", "nil"),
        ("potato", "out"),
        ("Pass", "out"),
    ) not in result

    assert (  # if ID is in, should have been delegated or bound...
        ("ID", "in"),
        ("potato@B", "nil"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result

    assert (  # Can't bind without receiving delegation without priority
        ("ID", "out"),
        ("potato@B", "nil"),
        ("potato@C", "nil"),
        ("potato", "out"),
        ("Pass", "out"),
    ) not in result

    assert result == [
        (  # ok, re-delegating
            ("ID", "in"),
            ("potato@B", "in"),
            ("potato@C", "out"),
            ("potato", "nil"),
            ("Pass", "out"),
        ),
        (  # ok, received delegation and binding
            ("ID", "in"),
            ("potato@B", "in"),
            ("potato@C", "nil"),
            ("potato", "out"),
            ("Pass", "out"),
        ),
        (  # propagating information to C
            ("ID", "in"),
            ("potato@B", "nil"),
            ("potato@C", "nil"),
            ("potato", "in"),
            ("Pass", "out"),
        ),
    ]


def test_Nonlive_action_schemas(Nonlive):
    RFQ = Nonlive.actions[0]
    RFQs = list(RFQ.schemas())  # RFQ
    print(RFQs)
    # can't have item in when sender has exclusive sayso
    assert (("ID", "in"), ("item", "in"), ("price", "in"), ("RFQ", "out")) not in RFQs
    assert RFQs == [
        (("ID", "in"), ("item", "out"), ("price", "in"), ("RFQ", "out")),
    ]

    Quotes = list(Nonlive.actions[1].schemas())
    print(Quotes)
    assert Quotes == [
        (("ID", "in"), ("item", "in"), ("price", "out"), ("Quote", "out"))
    ]


def test_langshaw_extend_schemas(Purchase):
    result = list(Purchase.extend_schemas(Purchase.actions[3]))
    pprint.pprint(result)
    assert result == [
        (
            ("ID", "in"),  # from action
            ("Quote", "in"),  # from action
            ("Reject", "out"),  # autonomy parameter
            ("Accept", "nil"),  # from conflict
            ("Deliver", "nil"),  # from conflict
        )
    ]


def test_langshaw_alt_parameters(Purchase):
    alts = Purchase.alt_parameters
    print(alts)
    assert alts == {"Reject": "done0", "Deliver": "done0"}


def test_langshaw_messages(Purchase, RFQ):
    ms = Purchase.messages(RFQ)
    result = list(m.format() for m in ms)
    pprint.pprint(result)
    assert result == [
        "B -> S: RFQ[in ID, out item@S, nil item, out RFQ]",
        "B -> S: RFQ[in ID, nil item@S, in item, out RFQ]",
        "B -> S: RFQ[in ID, nil item@S, out item, out RFQ]",
        "B -> S: RFQ[out ID, out item@S, nil item, out RFQ]",
        "B -> S: RFQ[out ID, nil item@S, out item, out RFQ]",
    ]


def test_langshaw_completion_messages(Purchase):
    ms = Purchase.completion_messages()
    result = list(m.format() for m in ms)
    pprint.pprint(result)
    assert result == [
        "B -> S: Reject#done0[in ID key, in Reject, out done0]",
        "Sh -> B: Deliver#done0[in ID key, in Deliver, out done0]",
        "Sh -> S: Deliver#done0[in ID key, in Deliver, out done0]",
    ]


def test_langshaw_nonlive(Nonlive):
    nonlive = """
who Buyer, Seller
what ID key, item, price

action
  Buyer: RFQ(ID, item, price)
  Seller: Quote(ID, item, price)

see
  Buyer: Quote
  Seller: RFQ

sayso
  Buyer: item
  Seller: price
"""

    p = Nonlive.to_bspl("Nonlive")
    print(p.format())
    assert not liveness(p)["live"]


def test_langshaw_repeat():
    repeat = """
who A, B
what ID key, thing

action
  A: One(ID, thing)
  A: Two(ID, thing)

sayso
  A: thing

see
  B: One, Two

nono
  One Two
"""
    p = Langshaw(load(repeat)).to_bspl("Repeat")
    print(p.format())
    assert liveness(p)["live"]


def test_langshaw_block_contra(BlockContra):
    block_contra = """
who A, B
what ID key, result

do
  A: Block(ID, result)
  B: Contra(ID, result)

sayso
  A > B: result

see
  A: Contra
  B: Block
"""
    p = Langshaw(load(block_contra)).to_bspl("BlockContra")
    print(p.format())
    assert liveness(p)["live"]


def test_langshaw_either_offer(EitherOffer):
    either_offer = """
who Buyer, Seller
what ID key, RFQ, Quote

do
 Buyer: RFQ(ID, item, price)
 Seller: Quote(ID, item, price)

see
  Buyer: Quote
  Seller: RFQ

sayso
 Buyer: item
 Buyer > Seller: price
"""

    p = EitherOffer.to_bspl("EitherOffer")
    print(p.format())
    assert liveness(p)["live"]


def test_langshaw_multikey(EitherOffer):
    multikey = """
who Buyer, Seller
what ID key, QID key, RFQ, Quote

do
 Buyer: RFQ(ID, item, price)
 Seller: Quote(ID, QID, item, price)

see
  Buyer: Quote
  Seller: RFQ

sayso
 Buyer: item
 Buyer > Seller: price
"""

    p = Langshaw(load(multikey)).to_bspl("MultiKey")
    print(p.format())
    assert liveness(p)["live"]


def test_liveness(Purchase):
    pprint.pprint(Purchase.spec)
    p = Purchase.to_bspl("Purchase")
    print(p.format())
    result = liveness(p)
    pprint.pprint(result)
    if "path" in result:
        pprint.pprint(list(m.format() for m in result["path"]))

    assert result["live"]
    assert False


def test_po_pay_cancel_ship():
    spec = """
  who Buyer, Seller
  what ID key, Ship or RescindConfirm

  do
  Buyer: Order(ID, item, price)
  Buyer: RescindRequest(ID, Order)
  Buyer: Pay(ID, Order)
  Seller: Ship(ID, Order)
  Seller: RescindConfirm(ID, RescindRequest)

  sayso
  Buyer: item
  Buyer: price

  nono
  RescindConfirm Ship

  see
    Seller: Order, RescindRequest, Pay
    Buyer: Ship, RescindConfirm
    """
    l = Langshaw(load(spec))
    pprint.pprint(l.spec)
    p = l.to_bspl("PoPayCancelShip")
    print(p.format())
    result = liveness(p)
    assert result["live"]
