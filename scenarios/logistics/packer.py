import logging
from bspl.adapter import Adapter
from configuration import systems, agents
from Logistics import Packed

adapter = Adapter("Packer", systems, agents)

logger = logging.getLogger("packer")
# logger.setLevel(logging.DEBUG)

@adapter.enabled(Packed)
async def pack(msg):
    msg["status"] = "packed"
    return msg

if __name__ == "__main__":
    logger.info("Starting Packer...")
    adapter.start()
