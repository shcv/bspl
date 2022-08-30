import asyncio
import logging
import pytest
import bspl
import bspl.parser
from bspl.adapter import Adapter
from bspl.adapter.store import Store

specification = bspl.parser.parse(
    """
Logistics {
  roles Merchant, Wrapper, Labeler, Packer
  parameters out orderID key, out itemID key, out item, out status
  private address, label, wrapping

  Merchant -> Labeler: RequestLabel[out orderID key, out address]
  Merchant -> Wrapper: RequestWrapping[in orderID key, out itemID key, out item]
  Wrapper -> Packer: Wrapped[in orderID key, in itemID key, in item, out wrapping]
  Labeler -> Packer: Labeled[in orderID key, in address, out label]
  Packer -> Merchant: Packed[in orderID key, in itemID key, in wrapping, in label, out status]
}
"""
)

logistics = specification.export("Logistics")
from Logistics import Packer, Wrapped, RequestLabel, Labeled, Packed

config = {
    Packer: ("localhost", 8001),
}

a = Adapter(Packer, logistics, config)  # for injection

logger = logging.getLogger("bspl")
logger.setLevel(logging.DEBUG)


def test_add():
    h = Store()
    m = Labeled(orderID=1, address="home", label="0001")
    h.add(m)
    assert m in [m for m in h.messages() if m.schema is Labeled]


def test_add_partial():
    h = Store()
    m = RequestLabel()
    h.add(m)
    m2 = RequestLabel()
    h.add(m2)
    print(h.contexts)
    assert len(list(h.messages())) == 1


def test_context_messages():
    h = Store()
    m = Labeled(orderID=1, address="home", label="0001")
    h.add(m)
    print(h.contexts)
    c = h.contexts["orderID"][1]
    print(list(c.messages()))
    assert m in c.messages()

    m2 = Wrapped(orderID=1, itemID=0, item="ball", wrapping="paper")
    h.add(m2)
    c2 = c["itemID"][0]
    print([m for m in c2.messages()])
    assert m2 in set(c2.messages())

    # message is not in parent context's messages list
    print([m for m in c.messages()])
    assert not m2 in set(c.messages())

    assert m in c.messages(Labeled)
    assert m not in c.messages(Wrapped)
    assert m in c.messages(orderID=1)
    assert m not in c.messages(orderID=2)


def test_context_all_messages():
    h = Store()
    m = Labeled(orderID=1, address="home", label="0001")
    h.add(m)
    print(h.contexts)
    c = h.contexts["orderID"][1]
    print(list(c.all_messages()))
    assert m in c.all_messages()

    m2 = Wrapped(orderID=1, itemID=0, item="ball", wrapping="paper")
    h.add(m2)
    print(h.contexts)
    print([m for m in c.messages()])
    assert m2 in set(c.all_messages())

    assert m in c.all_messages(Labeled)
    assert m not in c.all_messages(Wrapped)
    assert m in c.all_messages(orderID=1)
    assert m not in c.all_messages(orderID=2)


def test_context_bindings():
    h = Store()

    m = Wrapped(orderID=1, itemID=0, item="ball", wrapping="paper")
    h.add(m)
    print(h.contexts["orderID"][1].bindings)
    assert h.contexts["orderID"][1].bindings.get("orderID") == None
    assert (
        h.contexts["orderID"][1].subcontexts["itemID"][0].bindings.get("orderID") == 1
    )


def test_context_all_bindings():
    h = Store()
    m = Wrapped(orderID=1, itemID=0, item="ball", wrapping="paper")
    h.add(m)
    m2 = Wrapped(orderID=1, itemID=1, item="bat", wrapping="paper")
    h.add(m2)
    print(h.contexts["orderID"][1].all_bindings)
    items = h.contexts["orderID"][1].all_bindings["itemID"]
    assert items == [0, 1]
    assert h.contexts["orderID"][1].all_bindings["orderID"] == [1]


def test_matching_contexts():
    h = Store()
    m = Wrapped(orderID=1, itemID=0, item="ball", wrapping="paper")
    h.add(m)
    m2 = Wrapped(orderID=1, itemID=1, item="bat", wrapping="paper")
    h.add(m2)
    m3 = Labeled(orderID=1, address="home", label="0001")
    h.add(m3)
    contexts = h.matching_contexts(**m3.payload)
    print([c.bindings for c in contexts])
    assert len(contexts) == 3
