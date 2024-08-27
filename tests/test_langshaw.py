#!/usr/bin/env python3

import pytest
from bspl.parsers.langshaw import load
from bspl import langshaw
from bspl.langshaw import *
from bspl.verification import lpaths
import inspect
from bspl.verification.paths import liveness, safety, UoD, max_paths
import pprint, glob, os


@pytest.fixture(scope="module")
def Purchase():
    return Langshaw.load_file("samples/langshaw/purchase.lsh")


@pytest.fixture(scope="module")
def Nonlive():
    return Langshaw.load_file("samples/langshaw/nonlive.lsh")


@pytest.fixture(scope="module")
def BlockContra():
    return Langshaw.load_file("samples/langshaw/block-contra.lsh")


@pytest.fixture(scope="module")
def EitherOffer():
    return Langshaw.load_file("samples/langshaw/either-offer.lsh")


@pytest.fixture(scope="module")
def Redelegation():
    return Langshaw.load_file("samples/langshaw/redelegation.lsh")


@pytest.fixture(scope="module")
def RfqQuote():
    return Langshaw.load_file("samples/langshaw/rfq-quote.lsh")


@pytest.fixture(scope="module")
def RFQ(Purchase):
    return Purchase.actions[0]


@pytest.fixture(scope="module")
def Reject(Purchase):
    return Purchase.actions[3]


def test_grammar():
    load("Test\n\nwho: A\n")  # extra whitespace
    load("Test\n\nwhat: A, B, C or D")
    load("Test\n\ndo:\n  A: Act(a,b,c)\n")
    load("Test\n\ndo: A: Act(a,b,c)\n")


def test_load_langshaw_file():
    assert Langshaw.load_file("samples/langshaw/purchase.lsh")


def test_delegates():
    assert delegates("item@S")
    assert not delegates("item")


def test_validate(Purchase):
    assert validate(Purchase.spec)

    with pytest.raises(Exception) as e:
        validate(
            load(
                inspect.cleandoc(
                    """
        Test
        who A, B
        what a, b
        do:
            A: Send(a)
        sayso:
          A > B: a
          B: a
        """
                )
            )
        )
        assert e


def test_langshaw_get_clause(Purchase):
    who = langshaw.get_clause(Purchase.spec, "who")
    print(who)
    assert who

    what = langshaw.get_clause(Purchase.spec, "what")
    print(what)
    assert what

    actions = langshaw.get_clause(Purchase.spec, "actions")
    print(actions)
    assert actions


def test_langshaw_roles(Purchase):
    assert Purchase.roles == ["Buyer", "Seller", "Shipper"]


def test_langshaw_parameters(Purchase):
    assert Purchase.parameters == [
        "ID",
        "Reject",
        "Deliver",
    ]


def test_langshaw_keys(Purchase):
    assert list(Purchase.keys) == ["ID"]


def test_langshaw_actions(Purchase):
    assert len(Purchase.actions) == 6
    assert Purchase.actions[0].actor == "Buyer"
    assert Purchase.actions[0].name == "RFQ"
    assert Purchase.actions[0].parameters == ["ID", "item"]


def test_langshaw_conflicts(Purchase):
    # there are two conflicts in purchase - Accept/Reject and Deliver/Reject
    assert len(Purchase.conflicts) == 2
    # a conflict contains two actions
    assert len(Purchase.conflicts[0]) == 2
    assert Purchase.conflicts[0] == ["Accept", "Reject"]


def test_langshaw_nogos(RfqQuote):
    pprint.pprint(RfqQuote.spec)
    assert len(RfqQuote.nogos) == 1
    assert RfqQuote.nogos[0] == ["RescindRequest", "Goods"]


def test_langshaw_can_bind(Purchase):
    assert Purchase.can_bind("Buyer", "item")
    assert Purchase.can_bind("Seller", "item")
    assert Purchase.can_bind("Buyer", "RFQ")
    assert not Purchase.can_bind("Seller", "RFQ")
    assert not Purchase.can_bind("Shipper", "item")


def test_langshaw_can_be_delegated(Purchase):
    assert Purchase.can_be_delegated("Seller", "item")
    assert not Purchase.can_be_delegated("Buyer", "item")
    assert not Purchase.can_be_delegated("Buyer", "nonexistent-parameter")


def test_langshaw_delegates_to(Purchase):
    assert Purchase.delegates_to("Buyer", "item") == "Seller"
    assert Purchase.delegates_to("Seller", "item") == None
    assert Purchase.delegates_to("Shipper", "item") == None


def test_action_delegations(Purchase):
    assert list(Purchase.actions[0].delegations) == ["item@Seller"]
    assert list(Purchase.actions[1].delegations) == ["item@Seller", "price@Buyer"]


def test_action_expanded_parameters(Purchase):
    assert list(Purchase.actions[0].expanded_parameters) == [
        "ID",
        "item@Seller",
        "item",
        "RFQ",
    ]
    assert list(Purchase.actions[1].expanded_parameters) == [
        "ID",
        "item@Seller",
        "item",
        "price@Buyer",
        "price",
        "Quote",
    ]


def test_action_possibilities(RFQ, Reject):
    assert RFQ.possibilities("ID") == ["in", "out"]
    assert RFQ.possibilities("item") == ["in", "out", "nil"]
    assert Reject.possibilities("ID") == ["in", "out"]
    assert Reject.possibilities("Quote") == ["in"]


def test_action_explicit_dependencies(Purchase):
    # Quote doesn't depend on anything
    assert list(Purchase.actions[1].explicit_dependencies) == []
    # Reject depends on Quote
    assert list(Purchase.actions[3].explicit_dependencies) == [Purchase.actions[1]]


def test_langshaw_observes(Purchase):
    assert Purchase.observes("Buyer", "item")
    assert Purchase.observes("Seller", "item")
    # assert not Purchase.observes("Shipper", "price")


def test_langshaw_can_see(Purchase):
    a = Purchase.action
    assert Purchase.can_see("Buyer", a("RFQ"))
    assert Purchase.can_see("Buyer", a("Quote"))
    assert Purchase.can_see("Seller", a("RFQ"))
    # assert not Purchase.can_see("Shipper", a("Accept"))
    assert Purchase.can_see("Buyer", a("Deliver"))


def test_langshaw_recipients(Purchase):
    a = Purchase.actions
    assert Purchase.recipients(a[0]) == {"Seller", "Shipper"}  # RFQ
    assert Purchase.recipients(a[1]) == {"Buyer", "Shipper"}  # Quote
    # assert Purchase.recipients(a[2]) == {"Seller", "Shipper"}  # Accept


def test_action_columns(Purchase):
    from itertools import chain

    result = list(chain(*Purchase.actions[0].columns()))
    print(result)
    assert result


def test_action_all_schemas(Purchase):
    print(Purchase.actions[0])
    result = list(Purchase.actions[0].all_schemas())
    assert result == [
        (("ID", "in"), ("item@Seller", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "in"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "in"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "out"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "out"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "nil"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "in"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "in"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "out"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "out"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "nil"), ("item", "nil"), ("RFQ", "out")),
    ]


def test_ensure_priority(Redelegation):
    # roles are A, B, C
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
    assert f((("ID", "in"), ("item@Seller", "nil"), ("item", "out"), ("RFQ", "out")))


def test_RFQ_action_schemas(Purchase):
    result = list(Purchase.actions[0].schemas())  # RFQ
    print(result)
    assert result == [
        # can't have in for delegation to other role unless parameter is in
        # (("ID", "in"), ("item@Seller", "in"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "in"), ("item@Seller", "in"), ("item", "nil"), ("RFQ", "out")),
        # if delegation is out, parameter must be nil
        # (("ID", "in"), ("item@Seller", "out"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "in"), ("item@Seller", "out"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "out"), ("item@Seller", "out"), ("item", "out"), ("RFQ", "out")),
        # parameter and delegations cannot all be nil
        # (("ID", "in"), ("item@Seller", "nil"), ("item", "nil"), ("RFQ", "out")),
        # (("ID", "out"), ("item@Seller", "nil"), ("item", "nil"), ("RFQ", "out")),
        # can't have out keys with in parameters
        # (("ID", "out"), ("item@Seller", "in"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "out"), ("item@Seller", "in"), ("item", "out"), ("RFQ", "out")),
        # (("ID", "out"), ("item@Seller", "in"), ("item", "nil"), ("RFQ", "out")),
        # (("ID", "out"), ("item@Seller", "out"), ("item", "in"), ("RFQ", "out")),
        # (("ID", "out"), ("item@Seller", "nil"), ("item", "in"), ("RFQ", "out")),
        # ok
        (("ID", "in"), ("item@Seller", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@Seller", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@Seller", "nil"), ("item", "out"), ("RFQ", "out")),
    ]


def test_Quote_action_schemas(Purchase):
    result = list(Purchase.actions[1].schemas())  # RFQ
    pprint.pprint(result)
    assert (  # can bind item if delegated, and delegate price
        ("ID", "in"),
        ("item@Seller", "in"),
        ("item", "out"),
        ("price@Buyer", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) in result

    assert (  # can bind item if delegated, and price
        ("ID", "in"),
        ("item@Seller", "in"),
        ("item", "out"),
        ("price@Buyer", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) in result

    assert (  # ok; receives bound item, delegates price
        ("ID", "in"),
        ("item@Seller", "nil"),
        ("item", "in"),
        ("price@Buyer", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) in result

    assert (  # ok, receives item, binds price
        ("ID", "in"),
        ("item@Seller", "nil"),
        ("item", "in"),
        ("price@Buyer", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) in result

    assert (  # not ok; can't bind item without receiving delegation
        ("ID", "in"),
        ("item@Seller", "nil"),
        ("item", "out"),
        ("price@Buyer", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "in"),
        ("item@Seller", "nil"),
        ("item", "out"),
        ("price@Buyer", "nil"),
        ("price", "in"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "in"),
        ("item@Seller", "nil"),
        ("item", "out"),
        ("price@Buyer", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) not in result


def test_Accept_schemas(Purchase):
    result = list(Purchase.action("Accept").schemas())
    pprint.pprint(result)


def test_redelegation_schemas(Redelegation):
    Pass = Redelegation.actions[1]
    print("potato:", Pass.possibilities("potato"))
    print("potato@C:", Pass.possibilities("potato@C"))
    result = list(Pass.schemas())  # schemas for 'Pass' action
    assert (  # can't receive delegation without binding parameter or delegating
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "in"),
        ("potato@C", "nil"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self; can't have two delegations out
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "out"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "out"),
        ("potato@C", "nil"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self
        ("ID", "out"),
        ("Start", "in"),
        ("potato@B", "out"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result
    assert (  # can't delegate to self
        ("ID", "out"),
        ("Start", "in"),
        ("potato@B", "out"),
        ("potato@C", "nil"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result

    assert (  # can't re-delegate without receiving delegation
        ("ID", "out"),
        ("Start", "in"),
        ("potato@B", "nil"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result

    assert (  # if ID is in, should have been delegated or bound...
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "nil"),
        ("potato@C", "nil"),
        ("potato", "out"),
        ("Pass", "out"),
    ) not in result

    assert (  # if ID is in, should have been delegated or bound...
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "nil"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) not in result

    assert (  # Can't bind without receiving delegation without priority
        ("ID", "out"),
        ("Start", "in"),
        ("potato@B", "nil"),
        ("potato@C", "nil"),
        ("potato", "out"),
        ("Pass", "out"),
    ) not in result

    pprint.pprint(result)
    assert (  # ok, re-delegating
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "in"),
        ("potato@C", "out"),
        ("potato", "nil"),
        ("Pass", "out"),
    ) in result
    assert (  # ok, received delegation and binding
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "in"),
        ("potato@C", "nil"),
        ("potato", "out"),
        ("Pass", "out"),
    ) in result
    assert (  # propagating information to C
        ("ID", "in"),
        ("Start", "in"),
        ("potato@B", "nil"),
        ("potato@C", "nil"),
        ("potato", "in"),
        ("Pass", "out"),
    ) in result


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
    result = list(Purchase.extend_schemas(Purchase.action("Reject")))
    pprint.pprint(result)
    assert result == [
        (
            ("ID", "in"),  # from action
            ("Quote", "in"),  # from action
            ("Reject", "out"),  # autonomy parameter
            ("conflict0", "out"),  # from conflict with Accept
            ("conflict1", "out"),  # from conflict with Deliver
        )
    ]


def test_langshaw_alt_parameters(Purchase):
    alts = Purchase.alt_parameters
    print(alts)
    assert alts == {"Reject": "done0", "Deliver": "done0"}


def test_langshaw_private(Purchase):
    Purchase.to_bspl("Purchase")
    privates = Purchase.private
    print([str(p) for p in privates])
    assert privates == {
        "Accept",
        "Accept2",
        "Deliver",
        "Deliver2",
        "Instruct",
        "Instruct2",
        "Quote",
        "Quote2",
        "RFQ",
        "RFQ2",
        "Reject",
        "Reject2",
        "address",
        "fee",
        "item",
        "item@Seller",
        "price",
        "price@Buyer",
        # alt parameters (completion)
        "done0",
        # conflict parameters
        "conflict0",
        "conflict1",
    }


def test_langshaw_copies(Purchase):
    rfq = Purchase.actions[0]
    assert Purchase.copies(rfq) == ["RFQ2"]


def test_langshaw_messages(Purchase, RFQ):
    ms = Purchase.messages(RFQ)
    result = list(m.format() for m in ms)
    pprint.pprint(result)
    assert result  #  == [
    #     "B -> S: RFQ[in ID, in item@Seller, in item, out RFQ]",
    #     "B -> S: RFQ[in ID, out item@Seller, nil item, out RFQ]",
    #     "B -> S: RFQ[in ID, nil item@Seller, in item, out RFQ]",
    #     "B -> S: RFQ[in ID, nil item@Seller, out item, out RFQ]",
    #     "B -> S: RFQ[out ID, out item@Seller, nil item, out RFQ]",
    #     "B -> S: RFQ[out ID, nil item@Seller, out item, out RFQ]",
    # ]


def test_langshaw_completion_messages(Purchase):
    ms = Purchase.completion_messages()
    result = list(m.format() for m in ms)
    pprint.pprint(result)
    assert result == [
        "Buyer -> Seller: Reject-done0[in ID key, in Reject, out done0]",
        # "Buyer -> Shipper: Reject-done0[in ID key, in Reject, out done0]",
        "Shipper -> Buyer: Deliver-done0[in ID key, in Deliver, out done0]",
        # "Shipper -> Seller: Deliver-done0[in ID key, in Deliver, out done0]",
    ]


@pytest.mark.skip(reason="slow")
def test_langshaw_nonlive(Nonlive):
    print(Nonlive.source)
    p = Nonlive.to_bspl("Nonlive")
    print(p.format())
    assert list(Nonlive.messages(Nonlive.action("RFQ")))
    assert list(Nonlive.messages(Nonlive.action("Quote")))
    assert not liveness(p)["live"]


@pytest.mark.skip(reason="slow")
def test_langshaw_redelegation(Redelegation):
    pprint.pprint(Redelegation.source)
    p = Redelegation.to_bspl("Redelegation")
    print(p.format())
    result = liveness(p)
    pprint.pprint(result)
    assert result["live"]


def test_langshaw_repeat():
    repeat = """
Repeat
who A, B
what ID key, thing

do
  A: One(ID, thing)
  A: Two(ID, thing)
  B: See(ID, One, Two)

sayso
  A: thing

nono
  One Two
"""
    print(repeat)
    p = Langshaw(repeat).to_bspl("Repeat")
    print(p.format())
    result = liveness(p)
    pprint.pprint(result)
    assert result["live"]


def test_langshaw_block_contra(BlockContra):
    print(BlockContra.source)
    p = BlockContra.to_bspl("BlockContra")
    print(p.format())
    result = liveness(p)
    pprint.pprint(result)
    assert result["live"]


def test_langshaw_either_offer(EitherOffer):
    print(EitherOffer.source)
    p = EitherOffer.to_bspl("EitherOffer")
    print(p.format())
    result = liveness(p)
    pprint.pprint(result)
    assert result["live"]


def test_langshaw_multikey():
    multikey = """
Multikey
who Buyer, Seller
what ID key, QID key, RFQ, Quote

do
 Buyer: RFQ(ID, item, price)
 Seller: Quote(ID, QID, item, price)

sayso
 Buyer: item
 Buyer > Seller: price
"""

    p = Langshaw(multikey).to_bspl("MultiKey")
    print(p.format())
    assert liveness(p)["live"]


@pytest.mark.skip(reason="slow")
def test_langshaw_bspl_liveness(Purchase):
    print("langshaw:\n", Purchase.source)
    p = Purchase.to_bspl("Purchase")
    print("bspl:\n", p.format())
    print("messages:", len(p.messages))
    result = liveness(p)
    pprint.pprint(result)
    if "path" in result:
        pprint.pprint(list(m.format() for m in result["path"]))

    assert result["live"]

    result = safety(p)
    pprint.pprint(result)
    assert result["safe"]


def test_lpath_liveness(Purchase):
    print("langshaw:\n", Purchase.source)
    result = lpaths.liveness(Purchase, debug=True)
    pprint.pprint(result)
    if "path" in result:
        pprint.pprint(list(a.name for a in result["path"]))

    assert result["live"]

    result = lpaths.safety(Purchase)
    pprint.pprint(result)
    assert result["safe"]


def test_langshaw_purchase(Purchase):
    print("langshaw:\n", Purchase.source)
    pprint.pprint(lpaths.max_paths(lpaths.UoD(Purchase)))
    result = lpaths.liveness(Purchase)
    pprint.pprint(result)
    assert result["live"]


def test_langshaw_purchase2(Purchase):
    l = Langshaw.load_file("samples/langshaw/purchase2.lsh")
    print("langshaw:\n", l.source)
    pprint.pprint(lpaths.max_paths(lpaths.UoD(l)))
    result = lpaths.liveness(l, debug=True)
    pprint.pprint(result)
    assert result["live"]


def test_po_pay_cancel_ship():
    l = Langshaw.load_file("samples/langshaw/po-pay-cancel-ship.lsh")
    print("langshaw:\n", l.source)
    p = l.to_bspl("PoPayCancelShip")
    print("bspl:\n", p.format())
    print("messages:", len(p.messages))
    pprint.pprint(max_paths(UoD.from_protocol(p)))
    result = liveness(p)
    pprint.pprint(result)
    assert result["live"]


def test_rfq_quote():
    l = Langshaw.load_file("samples/langshaw/rfq-quote.lsh")
    print("langshaw:\n", l.source)
    pprint.pprint(l.spec)
    pprint.pprint(lpaths.max_paths(lpaths.UoD(l), debug=True))
    result = lpaths.liveness(l, debug=True)
    pprint.pprint(result)
    assert result["live"]


def test_minimal_rfq_quote():
    l = Langshaw(
        """
        MinimalRFQ
        who A, B
        what ID key, item
        do:
            A: RFQ(ID, item)
            A: Accept(ID, RFQ)
        sayso:
          A: item
        """
    )
    print("langshaw:\n", l.source)
    pprint.pprint(l.spec)
    result = lpaths.liveness(l, debug=True)
    pprint.pprint(result)
    assert result["live"]
    assert result["checked"] == 3
    assert result["maximal paths"] == 1


def test_exclusivity_diff(Purchase):
    for a in Purchase.actions:
        schemas = set(a.schemas())
        alt = set(filter(handle_exclusivity(a.parent, a.actor), a.schemas()))
        if schemas != alt:
            pprint.pprint(schemas.symmetric_difference(alt))


def test_langshaw_bspl_translation():
    # get list of langshaw protocol files
    lsh_files = glob.glob("samples/langshaw/*.lsh")
    protocols = []
    for lsh_file in lsh_files:
        l = Langshaw.load_file(lsh_file)
        # use the filename as the protocol name
        name = os.path.basename(lsh_file).split(".")[0]
        p = l.to_bspl(name)
        # count words in protocol
        bspl_words = len(re.findall(r"\w+", p.format()))
        langshaw_words = len(re.findall(r"\w+", l.source))
        protocols.append({"name": name, "bspl": bspl_words, "langshaw": langshaw_words})
    [
        print(f"{p['name'].capitalize()}, {p['langshaw']}, {p['bspl']}")
        for p in protocols
    ]


@pytest.mark.skip(reason="slow")
def test_langshaw_bspl_verification():
    # get list of langshaw protocol files
    lsh_files = glob.glob("samples/langshaw/*.lsh")
    # collect stats into list
    stats = []
    # foreach file, load it and convert to bspl
    for lsh_file in lsh_files:
        # skip purchase protocols; slow
        # if "purchase" in lsh_file:
        #     continue
        l = Langshaw.load_file(lsh_file)
        # use the filename as the protocol name
        name = os.path.basename(lsh_file).split(".")[0]
        p = l.to_bspl(name)
        # print(f"{name} bspl:\n", p.format())
        # collect results
        results = {
            "name": name,
            "messages": len(p.messages),
            "safe": safety(p)["safe"],
        }
        results.update(liveness(p))
        results["elapsed"] = round(results["elapsed"], 4)
        stats.append(results)
    # print stats
    print(format_table(stats))


def format_table(data):
    """Render list of dicts as a latex table"""
    columns = ["name", "checked", "maximal paths", "liveness", "safety"]
    rename = {
        "name": "Name",
        "messages": "Messages",
        "live": "Live",
        "safe": "Safe",
        "liveness": "Liveness",
        "safety": "Safety",
        "elapsed": "Time (ms)",
        "checked": "Nodes",
        "maximal paths": "Branches",
    }
    sizes = {c: max(max(len(str(d[c])), len(rename[c])) for d in data) for c in columns}

    def justify(field, c):
        return str(field).ljust(sizes[c], " ")

    # create header
    # result is a list of strings
    result = [" & ".join(justify(rename[c], c) for c in columns) + " \\\\ \\hline"]

    for entry in data:
        # create a row separated with & and terminated with \\
        result.append(" & ".join(justify(entry[c], c) for c in columns) + " \\\\")

    return "\n".join(result)


def format_table2(data):
    """Render latex table for lpaths verification"""
    for entry in data:
        entry["texname"] = "\\mname{" + entry["name"] + "}"
    columns = ["texname", "nodes", "branches", "liveness", "safety"]
    rename = {
        "texname": "Name",
        "liveness": "Liveness",
        "safety": "Safety",
        "nodes": "Nodes",
        "branches": "Branches",
    }
    sizes = {c: max(max(len(str(d[c])), len(rename[c])) for d in data) for c in columns}

    def justify(field, c):
        return str(field).ljust(sizes[c], " ")

    # create header
    # result is a list of strings
    result = [" & ".join(justify(rename[c], c) for c in columns) + " \\\\ \\midrule"]

    for entry in data:
        # create a row separated with & and terminated with \\
        result.append(" & ".join(justify(entry[c], c) for c in columns) + " \\\\")

    return "\n".join(result)


@pytest.mark.skip(reason="slow")
def test_langshaw_verification():
    # get list of langshaw protocol files
    lsh_files = glob.glob("samples/langshaw/*.lsh")
    # collect stats into list
    stats = {}
    # run multiple iterations
    for i in range(10):
        # foreach file, load it and convert to bspl
        for lsh_file in lsh_files:
            l = Langshaw.load_file(lsh_file)
            if l.name not in stats:
                stats[l.name] = []

            liveness = lpaths.liveness(l)
            safety = lpaths.safety(l)
            # collect results
            results = {
                **liveness,
                "name": l.name,
                "live": liveness["live"],
                "liveness": liveness["elapsed"],
                "safe": safety["safe"],
                "safety": safety["elapsed"],
            }
            stats[l.name].append(results)
    # average safety and liveness results
    averages = []
    for name, results in stats.items():
        nodes = round(sum(r["checked"] for r in results) / len(results), 1)
        branches = round(sum(r["maximal paths"] for r in results) / len(results), 1)
        liveness = round(sum(r["liveness"] for r in results) * 1000 / len(results), 1)
        safety = round(sum(r["safety"] for r in results) * 1000 / len(results), 1)
        averages.append(
            {
                "name": name,
                "nodes": "%g" % nodes,
                "branches": "%g" % branches,
                "liveness": liveness,
                "safety": safety,
            }
        )
    # print stats
    print("\n" + format_table2(averages))


@pytest.mark.skip(reason="slow")
def test_results():
    test_langshaw_verification()
