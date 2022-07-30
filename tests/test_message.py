#!/usr/bin/env python3

import asyncio
import logging
import pytest
import bspl.parser
from bspl.adapter.message import Message

specification = bspl.parser.parse(
    """
RFQ {
  roles C, S // Customer, Seller
  parameters out item key, out ship
  private price, payment

  C -> S: req[out item]
  S -> C: quote[in item, out price]
  C -> S: pay[in item, in price, out payment]
  S -> C: ship[in item, in payment, out ship]
}
"""
)
rfq = specification.export("RFQ")
from RFQ import C, S, req, quote


config = {
    C: ("localhost", 8001),
    S: ("localhost", 8002),
}

logger = logging.getLogger("bspl")
logger.setLevel(logging.DEBUG)


def test_message_complete():
    m = req()
    assert not m.complete

    m.bind(item=None)
    assert not m.complete

    m.bind(item="ball")
    assert m.complete


def test_complete_with_ins():
    # should never be complete with an in parameter bound to None
    m1 = quote()
    assert not m1.complete
    m1.bind(price=10)
    assert not m1.complete

    m2 = quote(item="ball")
    assert not m2.complete
    # should be complete if all ins and outs are bound
    m2.bind(price=10)
    assert m2.complete


def test_falsy_complete():
    m = req(item=0)
    assert m.complete
