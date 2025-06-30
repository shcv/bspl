#!/usr/bin/env python3

import pytest
from bspl.parsers.bspl import parse
from bspl.protocol import Message

specification = parse(
    """
RFQ {
  roles C, S // Customer, Seller
  parameters out item key, out ship
  private price, payment, address

  C -> S: req[out item]
  S -> C: quote[in item, out price]
  C -> S: pay[in item, in price, out payment, out address]
  S -> C: ship[in item, in payment, in address, out ship]
}
"""
)
rfq = specification.export("RFQ")
from RFQ import C, S, req, quote, pay


config = {
    C: ("localhost", 8001),
    S: ("localhost", 8002),
}

logger = logging.getLogger("bspl")
logger.setLevel(logging.DEBUG)


def test_message_init():
    m1 = Message(req)
    m2 = Message(req)

    assert m1.meta is not m2.meta


def test_message_complete():
    m = Message(req)
    assert not m.complete

    m.bind(item=None)
    assert not m.complete

    m.bind(item="ball")
    assert m.complete


def test_complete_with_ins():
    # should never be complete with an in parameter bound to None
    m1 = Message(quote)
    assert not m1.complete
    m1.bind(price=10)
    assert not m1.complete

    m2 = Message(quote, {"item": "ball"})
    assert not m2.complete
    # should be complete if all ins and outs are bound
    m2.bind(price=10)
    assert m2.complete


def test_falsy_complete():
    m = Message(req, {"item": 0})
    assert m.complete


def test_partial_bind():
    p = Message(req).partial()
    assert len(p.instances) == 0

    # should support multiple instances with different keys
    p.bind(item=1)
    assert len(p.instances) == 1
    p.bind(item=2)
    assert len(p.instances) == 2
    print(p.instances)
    assert p.instances[0]["item"] != p.instances[1]["item"]

    # partial with in key
    p = Message(quote, {"item": "ball"}).partial()
    with pytest.raises(Exception) as e:
        p.bind(item=1)
    assert str(e.value) == "Parameter item is in, not out"
    p.bind(price=10)
    p.bind(price=20)
    assert p.instances[0].payload != p.instances[1].payload

    # incomplete partial binding
    p = Message(pay, {"item": "ball", "price": 10}).partial()
    with pytest.raises(Exception) as e:
        p.bind(payment=10)
    assert (
        str(e.value)
        == "Bind must produce a complete instance: pay(item='ball',price=10,payment=10){system=None}"
    )
    p.bind(payment=10, address="home")
