from bungie import Adapter, Resend
from configuration import config, logistics
import uuid
import logging

logger = logging.getLogger("labeler")
# logging.getLogger('bungie').setLevel(logging.DEBUG)

adapter = Adapter(logistics.roles["Labeler"], logistics, config)
RequestLabel = logistics.messages["RequestLabel"]
Labeled = logistics.messages["Labeled"]


@adapter.reaction(RequestLabel)
async def request_label(message):
    payload = {
        "orderID": message.payload["orderID"],
        "address": message.payload["address"],
        "label": str(uuid.uuid4()),
    }
    adapter.send(payload, Labeled)


if __name__ == "__main__":
    logger.info("Starting Labeler...")
    # adapter.load_policy_file("policies.yaml")
    adapter.start()
