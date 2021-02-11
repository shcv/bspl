import asyncio
import logging
import pytest
from protocheck import bspl
from bungie.adapter import Adapter, Message
from bungie.emitter import Emitter

specification = bspl.parse(
    """
Order {
  roles C, S // Customer, Seller
  parameters out item key, out done

  C -> S: Buy[out item]
  S -> C: Deliver[in item, out done]
}

With-Reject {
  roles C, S
  parameters out item key, out done

  Order(C, S, out item, out done)
  S -> C: Reject[in item, out done]
}
"""
)

with_reject = specification.protocols["With-Reject"]

config = {
    with_reject.roles["C"]: ("localhost", 8001),
    with_reject.roles["S"]: ("localhost", 8002),
}

logger = logging.getLogger("bungie")
logger.setLevel(logging.DEBUG)


@pytest.mark.asyncio
async def test_receive_process():
    a = Adapter(with_reject.roles["S"], with_reject, config)
    await a.task()
    await a.receive({"item": "ball"})
    await a.stop()

    print(f"all bindings: {a.history.all_bindings}")


@pytest.mark.asyncio
async def test_send_process():
    a = Adapter(with_reject.roles["C"], with_reject, config, emitter=Emitter())
    m = Message(with_reject.messages["Buy"], {"item": "ball"})
    await a.task()
    await a.process_send(m)
    await a.stop()


@pytest.mark.asyncio
async def test_match():
    """Test that the schema.match(**params) method works"""
    # create adapter and inject methods
    a = Adapter(with_reject.roles["S"], with_reject, config)
    await a.task()
    # make sure there's a Buy in the history
    await a.receive({"item": "ball"})
    ms = with_reject.messages["Deliver"].match(item="ball")
    assert len(ms) > 0
    await a.stop()
