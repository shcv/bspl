import asyncio
import logging
import pytest
import bspl.parsers.bspl
from bspl.adapter import Adapter
from bspl.adapter.message import Message
from bspl.adapter.emitter import Emitter, MockEmitter
from bspl.adapter.receiver import Receiver, MockReceiver
from bspl.adapter.event import InitEvent

logger = logging.getLogger("bspl")
logger.setLevel(logging.DEBUG)


@pytest.fixture(scope="module")
def RFQ():
    return bspl.parsers.bspl.parse(
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
            "roles": {S: "S", C: "C"},
        }
    }


@pytest.fixture(scope="module")
def agents():
    return {
        "C": [("localhost", 8001)],
        "S": [("localhost", 8002)],
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
async def test_receive_process(systems, agents, req):
    # Create the adapter with mock network components to avoid binding to real ports
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()
    a = Adapter("S", systems, agents, emitter=mock_emitter, receiver=mock_receiver)
    await a.receive(req(item="ball").serialize())
    await a.update()

    print(f"messages: {a.history.messages()}")


@pytest.mark.asyncio
async def test_send(systems, agents, req):
    # Create the adapter with mock network components to avoid binding to real ports
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()
    a = Adapter("C", systems, agents, emitter=mock_emitter, receiver=mock_receiver)
    m = req(item="ball")
    await a.send(m)


@pytest.mark.asyncio
async def test_match(RFQ, systems, agents, req, quote, ship):
    """Test that the schema.match(**params) method works"""
    # Create the adapter with mock network components to avoid binding to real ports
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()
    a = Adapter("S", systems, agents, emitter=mock_emitter, receiver=mock_receiver)
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
async def test_enabled_initiators(systems, agents, req):
    # Create the adapter with mock network components to avoid binding to real ports
    mock_emitter = MockEmitter()
    mock_receiver = MockReceiver()
    a = Adapter("C", systems, agents, emitter=mock_emitter, receiver=mock_receiver)
    await a.process(InitEvent())

    print(list(a.enabled_messages.messages()))
    assert len(list(a.enabled_messages.messages())) == 1
    assert next(a.enabled_messages.messages()).schema == req
