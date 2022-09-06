import asyncio
import logging
import pytest
import bspl.parser
from bspl.adapter import Adapter
from bspl.adapter.message import Message
from bspl.adapter.emitter import Emitter

logger = logging.getLogger("bspl")
logger.setLevel(logging.DEBUG)


@pytest.fixture(scope="module")
def RFQ():
    return bspl.parser.parse(
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
    ).protocols["RFQ"]


@pytest.fixture(scope="module")
def C(RFQ):
    return RFQ.roles["C"]


@pytest.fixture(scope="module")
def S(RFQ):
    return RFQ.roles["S"]


@pytest.fixture(scope="module")
def systems(C, S, RFQ):
    return {
        0: {
            "protocol": RFQ,
            "agents": {
                "C": ("localhost", 8001),
                "S": ("localhost", 8002),
            },
            "roles": {S: "S", C: "C"},
        }
    }


@pytest.fixture(scope="module")
def req(RFQ):
    return RFQ.messages["req"]


@pytest.fixture(scope="module")
def quote(RFQ):
    return RFQ.messages["quote"]


@pytest.fixture(scope="module")
def ship(RFQ):
    return RFQ.messages["ship"]


@pytest.mark.asyncio
async def test_receive_process(systems, req):
    a = Adapter("S", systems)
    await a.receive(req(item="ball").serialize())
    await a.update()

    print(f"messages: {a.history.messages()}")


@pytest.mark.asyncio
async def test_send(systems, req):
    a = Adapter("C", systems)
    m = req(item="ball")
    await a.send(m)


@pytest.mark.asyncio
async def test_match(RFQ, systems, req, quote, ship):
    """Test that the schema.match(**params) method works"""
    # create adapter and inject methods
    a = Adapter("S", systems)
    # make sure there's a req in the history
    m = req(item="ball")
    await a.receive(m.serialize())

    # There should be one enabled 'quote'
    ms = quote.match(m)
    assert len(ms) == 1

    # But not any enabled 'ship's
    ms2 = ship.match(m)
    assert len(ms2) == 0


@pytest.mark.asyncio
async def test_enabled_initiators(systems, req):
    a = Adapter("s", systems)
    a.compute_enabled({})

    print(list(a.enabled_messages.messages()))
    assert len(list(a.enabled_messages.messages())) == 1
    assert next(a.enabled_messages.messages()).schema == req
