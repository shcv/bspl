#!/usr/bin/env python3

import asyncio
import pytest
import bspl.parser
from bspl.adapter.schema import *


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


def test_instantiate():
    i = instantiate("test")
    assert i(req, item="ball").payload == {"item": "ball"}
    assert i(req, "ball").payload == {"item": "ball"}
