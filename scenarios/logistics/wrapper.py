import logging
from bspl.adapter import Adapter
from configuration import systems, agents
from Logistics import Wrapped, RequestWrapping

adapter = Adapter("Wrapper", systems, agents)

logger = logging.getLogger("wrapper")
# logger.setLevel(logging.DEBUG)

@adapter.reaction(RequestWrapping)
async def wrap(msg):
    await adapter.send(
        Wrapped(
            wrapping="bubblewrap" if msg["item"] in ["plate", "glass"] else "paper",
            **msg.payload
        )
    )
    return msg

if __name__ == "__main__":
    logger.info("Starting Wrapper...")
    adapter.start()
