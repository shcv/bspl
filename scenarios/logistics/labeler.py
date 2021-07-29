from bungie import Adapter, Remind
from configuration import config, logistics, Labeled
import uuid
import logging

logger = logging.getLogger("labeler")
# logging.getLogger('bungie').setLevel(logging.DEBUG)

adapter = Adapter(logistics.roles["Labeler"], logistics, config)
RequestLabel = logistics.messages["RequestLabel"]


async def decision_handler(enabled, event):
    emissions = set()
    for m in enabled.messages:
        if m.schema == Labeled:
            m.bind(label=str(uuid.uuid4()))
            emissions.add(m)
    return emissions


adapter.decision_handler = decision_handler


if __name__ == "__main__":
    logger.info("Starting Labeler...")
    adapter.start()
