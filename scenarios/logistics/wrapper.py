from bungie import Adapter, Resend
from configuration import config, logistics
import logging

logger = logging.getLogger("wrapper")
# logging.getLogger('bungie').setLevel(logging.DEBUG)

adapter = Adapter(logistics.roles["Wrapper"], logistics, config)
RequestWrapping = logistics.messages["RequestWrapping"]
Wrapped = logistics.messages["Wrapped"]


@adapter.reaction(RequestWrapping)
async def request_wrapping(message):
    item = message.payload["item"]

    payload = {
        "orderID": message.payload["orderID"],
        "itemID": message.payload["itemID"],
        "item": item,
        "wrapping": "bubblewrap" if item in ["plate", "glass"] else "paper",
    }
    adapter.send(payload, Wrapped)


if __name__ == "__main__":
    logger.info("Starting Wrapper...")
    # adapter.load_policy_file("policies.yaml")
    adapter.start()
