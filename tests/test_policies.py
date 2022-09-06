import pytest
import yaml
import asyncio
import logging
import bspl
import bspl.parser
from bspl.adapter import Adapter
from bspl.adapter.emitter import MockEmitter
from bspl.adapter.policies import *
from bspl.adapter.message import Message
from bspl.adapter.store import Store

specification = bspl.parser.parse(
    """
Order {
  roles C, S // Customer, Seller
  parameters out item key, out done
  private extra, ackID, remID

  C -> S: Buy[out item]
  S -> C: BuyAck[in item, out ackID key]
  C -> S: BuyReminder[in item, out remID key]

  S -> C: Deliver[in item, out done]
  S -> C: Extra[in item, out extra]
}

With-Reject {
  roles C, S
  parameters out item key, out done

  Order(C, S, out item, out done)
  S -> C: Reject[in item, out done]
}
"""
)


order = specification.export("Order")
from Order import C, S, Buy, Deliver, BuyAck, BuyReminder, Extra

systems = {
    0: {
        "protocol": order,
        "agents": {"C": ("localhost", 8001), "S": ("localhost", 8001)},
        "roles": {C: "C", S: "S"},
    }
}
Map = {
    "reminders": {Buy: (BuyReminder, "remID")},
}

logger = logging.getLogger("bspl")
logger.setLevel(logging.DEBUG)


@pytest.mark.asyncio
async def test_remind_until_received():
    r = Remind(Buy).With(Map).until.received(Deliver)
    assert r
    assert r.expectations  # reactors for handling reception

    # Buy without Deliver should be resent
    a = Adapter("C", systems, emitter=MockEmitter())
    a.add_policies(r)
    assert a.reactors[Buy]

    m = Buy(item="shoe")
    await a.send(m)
    await a.update()
    assert r.active
    selected = r.run(a.history)
    assert selected
    assert selected[0].schema == BuyReminder

    # Buy with Deliver should not
    await a.receive(Deliver(item="shoe", done="yep", system=0).serialize())
    await a.update()
    selected = r.run(a.history)
    assert not selected


@pytest.mark.asyncio
async def test_remind_until_conjunction():
    r = Remind(Buy).With(Map).until.received(Deliver, Extra)
    assert r
    assert r.expectations  # reactors for handling reception

    # Buy without Deliver should be resent
    a = Adapter("C", systems, emitter=MockEmitter())
    a.add_policies(r)
    assert a.reactors[Buy]
    m = Buy(item="shoe", system=0)
    await a.send(m)
    await a.update()
    assert r.active
    selected = r.run(a.history)
    assert selected
    assert selected[0].schema == BuyReminder

    # Buy with only Deliver should still be resent
    await a.receive(Deliver(item="shoe", done="yep", system=0).serialize())
    await a.update()
    selected = r.run(a.history)
    assert selected

    # Buy with both Deliver and Extra should not be resent
    await a.receive(Extra(item="shoe", extra="totally", system=0).serialize())
    await a.update()
    selected = r.run(a.history)
    assert not selected


def test_parser():
    p = model.parse("remind labeler of RequestLabel until received Packed")
    print(p)
    assert p


def test_from_ast():
    ast = model.parse("remind seller of Buy until received Deliver")
    print(ast)
    policy = from_ast(order, ast)
    assert policy
    assert type(policy) == Remind
    assert "Buy" in [m.name for m in policy.schemas]
    assert not policy.reactive

    ast = model.parse("remind seller of Buy until received Deliver or received Extra")
    print(ast)
    policy = from_ast(order, ast)
    assert policy
    assert type(policy) == Remind
    assert "Buy" in [m.name for m in policy.schemas]
    assert not policy.reactive


def test_policy_parser():
    reminder_policy = """
    - policy: remind S of Buy until Deliver
      when: 0 0 * * *
      max tries: 5
    """
    assert parse(order, reminder_policy)
