import logging
import uuid
from bspl.adapter import Adapter
from configuration import systems, agents
from Logistics import Labeled, RequestLabel

adapter = Adapter("Labeler", systems, agents)

logger = logging.getLogger("labeler")
# logger.setLevel(logging.DEBUG)

@adapter.reaction(RequestLabel)
async def label(msg):
    await adapter.send(Labeled(label=str(uuid.uuid4()), **msg.payload))
    return msg

if __name__ == "__main__":
    logger.info("Starting Labeler...")
    adapter.start()
