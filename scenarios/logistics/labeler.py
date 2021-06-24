from bungie import Adapter, Remind
from configuration import config, logistics, Labeled
import uuid
import logging

logger = logging.getLogger("labeler")
# logging.getLogger('bungie').setLevel(logging.DEBUG)

adapter = Adapter(logistics.roles["Labeler"], logistics, config)
RequestLabel = logistics.messages["RequestLabel"]


@adapter.enabled(Labeled)
async def labeled(msg):
    msg["label"] = str(uuid.uuid4())
    logger.info(msg)
    return msg


if __name__ == "__main__":
    logger.info("Starting Labeler...")
    # adapter.load_policy_file("policies.yaml")
    adapter.start()
