import pytest
import yaml
import asyncio
from protocheck import bspl
from bungie.policies import *
from bungie.adapter import Message
from bungie.history import History

specification = bspl.parse("""
Order {
  roles C, S // Customer, Seller
  parameters out item key, out done
  private extra

  C -> S: Buy[out item]
  S -> C: Deliver[in item, out done]
  S -> C: Extra[in item, out extra]
}

With-Reject {
  roles C, S
  parameters out item key, out done

  Order(C, S, out item, out done)
  S -> C: Reject[in item, out done]
}
""")

Order = specification.protocols['Order']
with_reject = specification.protocols['With-Reject']
Buy = Order.messages['Buy']
Deliver = Order.messages['Deliver']


def test_resend_until_received():
    r = Resend(Buy).until.received(Deliver)
    assert(r)
    assert(r.proactors)
    assert(not r.reactors)

    # Buy without Deliver should be resent
    h = History()
    m = Message(Buy, {'item': 'shoe'})
    h.observe(m)
    selected = r.run(h)
    assert(selected)
    assert(m in selected)

    # Buy with Deliver should not
    m2 = Message(Deliver, {'item': 'shoe', 'done': 'yep'})
    h.observe(m2)
    selected = r.run(h)
    assert(not selected)


def test_resend_until_ack():
    r = Resend(Buy).until.acknowledged
    assert(r)
    assert(r.proactors)
    assert(not r.reactors)

    # Buy without acknowledgement should be resent
    h = History()
    m = Message(Buy, {'item': 'shoe'})
    h.observe(m)
    selected = r.run(h)
    assert(selected)
    assert(m in selected)

    # Should not be resent after acknowledgement
    h.acknowledge(m)
    selected = r.run(h)
    assert(not selected)


def test_resend_until_conjunction():
    Extra = Order.messages['Extra']
    r = Resend(Buy).until.received(Deliver, Extra)

    # Buy without Deliver should be resent
    h = History()
    m = Message(Buy, {'item': 'shoe'})
    h.observe(m)
    selected = r.run(h)
    assert(selected)
    assert(m in selected)

    # Buy with only Deliver should still be resent
    m2 = Message(Deliver, {'item': 'shoe', 'done': 'yep'})
    h.observe(m2)
    selected = r.run(h)
    assert(m in selected)

    # Buy with both Deliver and Extra should not be resent
    m3 = Message(Extra, {'item': 'shoe', 'extra': 'totally'})
    h.observe(m3)
    selected = r.run(h)
    assert(m not in selected)


def test_parser():
    p = model.parse(
        "resend RequestLabel, RequestWrapping until received Packed")
    print(p)
    assert p


def test_from_ast():
    ast = model.parse(
        "resend Buy until received Deliver")
    print(ast)
    policy = from_ast(Order, ast)
    assert(policy)
    assert(type(policy) == Resend)
    assert('Buy' in [m.name for m in policy.schemas])
    assert(not policy.reactive)
    print([e for e in ast['events']])
    assert(policy.proactors[0].__name__ == 'process_received')

    ast = model.parse(
        "resend Buy until received Deliver or received Extra")
    print(ast)
    policy = from_ast(Order, ast)
    assert(policy)
    assert(type(policy) == Resend)
    assert('Buy' in [m.name for m in policy.schemas])
    assert(not policy.reactive)
    print([e for e in ast['events']])
    assert(policy.proactors[0].__name__ == 'process_received')
