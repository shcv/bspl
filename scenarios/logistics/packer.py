"""
This agent combines wrapped items with their labels to create the final package.
"""

import logging
from bspl.adapter import Adapter
from configuration import systems, agents
from Logistics import Packed

adapter = Adapter("Packer", systems, agents)

logger = logging.getLogger("packer")
# logger.setLevel(logging.DEBUG)

@adapter.enabled(Packed)
async def pack(msg):
    """Handles enabled Packed messages by setting their status."""
    msg["status"] = "packed"
    return msg

if __name__ == "__main__":
    logger.info("Starting Packer...")
    adapter.start()
