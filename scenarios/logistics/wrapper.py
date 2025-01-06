"""
This agent handles wrapping requests by choosing appropriate wrapping material based on item type.
"""

import logging
from bspl.adapter import Adapter
from configuration import systems, agents
from Logistics import Wrapped, RequestWrapping

adapter = Adapter("Wrapper", systems, agents)

logger = logging.getLogger("wrapper")
# logger.setLevel(logging.DEBUG)

@adapter.reaction(RequestWrapping)
async def wrap(msg):
    """Handles wrapping requests by selecting appropriate material (bubblewrap for fragile items)."""
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
