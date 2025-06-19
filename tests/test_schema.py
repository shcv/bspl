#!/usr/bin/env python3

import asyncio
import pytest
import bspl.parsers.bspl
from bspl.adapter import Adapter
from bspl.adapter.schema import *


specification = bspl.parsers.bspl.parse(
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
    agents = {"C": ("localhost", 8000)}
    systems = {0: {"protocol": rfq, "roles": {}}}
    i = instantiate(Adapter("C", systems, agents))
    assert i(req, item="ball").payload == {"item": "ball"}
    assert i(req, "ball").payload == {"item": "ball"}
