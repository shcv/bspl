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
    return Langshaw.load_file("samples/tests/langshaw/purchase.lsh")


@pytest.fixture(scope="module")
def Nonlive():
    return Langshaw.load_file("samples/tests/langshaw/nonlive.lsh")


@pytest.fixture(scope="module")
def BlockContra():
    return Langshaw.load_file("samples/tests/langshaw/block-contra.lsh")


@pytest.fixture(scope="module")
def EitherOffer():
    return Langshaw.load_file("samples/tests/langshaw/either-offer.lsh")


@pytest.fixture(scope="module")
def Redelegation():
    return Langshaw.load_file("samples/tests/langshaw/redelegation.lsh")


@pytest.fixture(scope="module")
def RfqQuote():
    return Langshaw.load_file("samples/tests/langshaw/rfq-quote.lsh")


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


def test_load_file():
    assert Langshaw.load_file("samples/tests/langshaw/purchase.lsh")


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
    assert Purchase.roles == ["B", "S", "Sh"]


def test_langshaw_parameters(Purchase):
    assert Purchase.parameters == [
        "ID",
        "Reject",
        "Deny",
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
            "Deny",
            "item@S",
            "price@B",
        ]
    )


def test_langshaw_keys(Purchase):
    assert list(Purchase.keys) == ["ID"]


def test_langshaw_actions(Purchase):
    assert len(Purchase.actions) == 7
    assert Purchase.actions[0].actor == "B"
    assert Purchase.actions[0].name == "RFQ"
    assert Purchase.actions[0].parameters == ["ID", "item"]


def test_langshaw_conflicts(Purchase):
    assert len(Purchase.conflicts) == 3
    assert len(Purchase.conflicts[0]) == 2
    assert Purchase.conflicts[0] == ["Accept", "Reject"]


def test_langshaw_nogos(RfqQuote):
    pprint.pprint(RfqQuote.spec)
    assert len(RfqQuote.nogos) == 1
    assert RfqQuote.nogos[0] == ["RescindRequest", "Goods"]


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
        "RFQ",
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


def test_action_explicit_dependencies(Purchase):
    assert list(Purchase.actions[0].explicit_dependencies) == []
    assert list(Purchase.actions[1].explicit_dependencies) == [Purchase.actions[0]]


def test_langshaw_observes(Purchase):
    assert Purchase.observes("B", "item")
    assert Purchase.observes("S", "item")
    assert not Purchase.observes("Sh", "price")


def test_langshaw_can_see(Purchase):
    a = Purchase.action
    assert Purchase.can_see("B", a("RFQ"))
    assert Purchase.can_see("B", a("Quote"))
    assert Purchase.can_see("S", a("RFQ"))
    assert not Purchase.can_see("Sh", a("Accept"))
    assert Purchase.can_see("B", a("Deliver"))


def test_langshaw_recipients(Purchase):
    a = Purchase.actions
    assert Purchase.recipients(a[0]) == {"S"}  # RFQ
    assert Purchase.recipients(a[1]) == {"B"}  # Quote
    # assert Purchase.recipients(a[2]) == {"S", "Sh"}  # Accept


def test_action_columns(Purchase):
    from itertools import chain

    result = list(chain(*Purchase.actions[0].columns()))
    print(result)
    assert result


def test_action_all_schemas(Purchase):
    print(Purchase.actions[0])
    result = list(Purchase.actions[0].all_schemas())
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
        # can't have in for delegation to other role unless parameter is in
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
        (("ID", "in"), ("item@S", "in"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "nil"), ("item", "in"), ("RFQ", "out")),
        (("ID", "in"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "out"), ("item", "nil"), ("RFQ", "out")),
        (("ID", "out"), ("item@S", "nil"), ("item", "out"), ("RFQ", "out")),
    ]


def test_Quote_action_schemas(Purchase):
    result = list(Purchase.actions[1].schemas())  # RFQ
    pprint.pprint(result)
    assert (  # can bind item if delegated, and delegate price
        ("ID", "in"),
        ("RFQ", "in"),
        ("item@S", "in"),
        ("item", "out"),
        ("price@B", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) in result

    assert (  # can bind item if delegated, and price
        ("ID", "in"),
        ("RFQ", "in"),
        ("item@S", "in"),
        ("item", "out"),
        ("price@B", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) in result

    assert (  # ok; receives bound item, delegates price
        ("ID", "in"),
        ("RFQ", "in"),
        ("item@S", "nil"),
        ("item", "in"),
        ("price@B", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) in result

    assert (  # ok, receives item, binds price
        ("ID", "in"),
        ("RFQ", "in"),
        ("item@S", "nil"),
        ("item", "in"),
        ("price@B", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) in result

    assert (  # not ok; can't bind item without receiving delegation
        ("ID", "in"),
        ("RFQ", "in"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "out"),
        ("price", "nil"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "in"),
        ("RFQ", "in"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "nil"),
        ("price", "in"),
        ("Quote", "out"),
    ) not in result

    assert (  # not ok, can't bind item without receiving delegation
        ("ID", "in"),
        ("RFQ", "in"),
        ("item@S", "nil"),
        ("item", "out"),
        ("price@B", "nil"),
        ("price", "out"),
        ("Quote", "out"),
    ) not in result


def test_Accept_schemas(Purchase):
    result = list(Purchase.action("Accept").schemas())
    pprint.pprint(result)


def test_redelegation(Redelegation):
    result = list(Redelegation.actions[1].schemas())  # Pass
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
            ("Accept", "nil"),  # from conflict
            ("Deliver", "nil"),  # from conflict
        )
    ]


def test_langshaw_alt_parameters(Purchase):
    alts = Purchase.alt_parameters
    print(alts)
    assert alts == {"Reject": "done0", "Deliver": "done0", "Deny": "done0"}


def test_langshaw_messages(Purchase, RFQ):
    ms = Purchase.messages(RFQ)
    result = list(m.format() for m in ms)
    pprint.pprint(result)
    assert result  #  == [
    #     "B -> S: RFQ[in ID, in item@S, in item, out RFQ]",
    #     "B -> S: RFQ[in ID, out item@S, nil item, out RFQ]",
    #     "B -> S: RFQ[in ID, nil item@S, in item, out RFQ]",
    #     "B -> S: RFQ[in ID, nil item@S, out item, out RFQ]",
    #     "B -> S: RFQ[out ID, out item@S, nil item, out RFQ]",
    #     "B -> S: RFQ[out ID, nil item@S, out item, out RFQ]",
    # ]


def test_langshaw_completion_messages(Purchase):
    ms = Purchase.completion_messages()
    result = list(m.format() for m in ms)
    pprint.pprint(result)
    assert result == [
        "B -> S: Reject#done0[in ID key, in Reject, out done0]",
        "B -> Sh: Reject#done0[in ID key, in Reject, out done0]",
        "S -> B: Deny#done0[in ID key, in Deny, out done0]",
        "S -> Sh: Deny#done0[in ID key, in Deny, out done0]",
        "Sh -> B: Deliver#done0[in ID key, in Deliver, out done0]",
        "Sh -> S: Deliver#done0[in ID key, in Deliver, out done0]",
    ]


def test_langshaw_nonlive(Nonlive):
    print(Nonlive.source)
    p = Nonlive.to_bspl("Nonlive")
    print(p.format())
    assert list(Nonlive.messages(Nonlive.action("RFQ")))
    assert list(Nonlive.messages(Nonlive.action("Quote")))
    assert not liveness(p)["live"]


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


def test_liveness(Purchase):
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


def test_po_pay_cancel_ship():
    l = Langshaw.load_file("samples/tests/langshaw/po-pay-cancel-ship.lsh")
    print("langshaw:\n", l.source)
    p = l.to_bspl("PoPayCancelShip")
    print("bspl:\n", p.format())
    print("messages:", len(p.messages))
    pprint.pprint(max_paths(UoD.from_protocol(p)))
    result = liveness(p)
    pprint.pprint(result)
    assert result["live"]


def test_rfq_quote():
    l = Langshaw.load_file("samples/tests/langshaw/rfq-quote.lsh")
    print("langshaw:\n", l.source)
    pprint.pprint(l.spec)
    pprint.pprint(lpaths.max_paths(lpaths.UoD(l), debug=True))
    result = lpaths.liveness(l, debug=True)
    pprint.pprint(result)
    assert result["live"]
    assert False


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


def test_langshaw_protocols():
    # get list of langshaw protocol files
    lsh_files = glob.glob("samples/tests/langshaw/*.lsh")
    # collect stats into list
    stats = []
    # foreach file, load it and convert to bspl
    for lsh_file in lsh_files:
        l = Langshaw.load_file(lsh_file)
        # use the filename as the protocol name
        name = os.path.basename(lsh_file).split(".")[0]
        p = l.to_bspl(name)
        # collect results
        results = {
            "name": name,
            "messages": len(p.messages),
            "live": liveness(p)["live"],
        }
        results.update(safety(p))
        results["elapsed"] = round(results["elapsed"], 4)
        stats.append(results)
    # print stats
    print(format_table(stats))


def format_table(data):
    """Render list of dicts as a latex table"""
    columns = list(data[0].keys())
    sizes = {c: max(max(len(str(d[c])), len(c)) for d in data) for c in columns}

    def justify(field, c):
        return str(field).ljust(sizes[c], " ")

    # create header
    # result is a list of strings
    result = [" & ".join(justify(c, c) for c in columns) + " \\\\ \\hline"]

    for entry in data:
        # create a row separated with & and terminated with \\
        result.append(" & ".join(justify(entry[c], c) for c in columns) + " \\\\")

    return "\n".join(result)


def test_lpaths():
    # get list of langshaw protocol files
    lsh_files = glob.glob("samples/tests/langshaw/*.lsh")
    # collect stats into list
    stats = []
    # foreach file, load it and convert to bspl
    for lsh_file in lsh_files:
        print(lsh_file)
        l = Langshaw.load_file(lsh_file)
        print(l.name)
        print(lpaths.all_paths(lpaths.UoD(l)))

        # collect results
        results = {
            "name": l.name,
            "live": lpaths.liveness(l, debug=True)["live"],
        }
        results.update(lpaths.safety(l, debug=True))
        results["elapsed"] = round(results["elapsed"], 4)
        stats.append(results)
    # print stats
    print(format_table(stats))
    assert False
