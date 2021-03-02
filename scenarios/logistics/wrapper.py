from bungie import Adapter
from configuration import config, logistics, Map
import logging

from bungie.policies import Acknowledge

logger = logging.getLogger("wrapper")
# logging.getLogger('bungie').setLevel(logging.DEBUG)

adapter = Adapter(logistics.roles["Wrapper"], logistics, config)
RequestWrapping = logistics.messages["RequestWrapping"]
Wrapped = logistics.messages["Wrapped"]

from Logistics import RequestWrappingReminder

# from Logistics import RequestWrappingAck


@adapter.reaction(RequestWrapping, RequestWrappingReminder)
# @adapter.reaction(RequestWrapping)
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

    # acknowledge Complain
    # adapter.add_policies(
    #     Acknowledge(RequestWrapping).Map(Map),
    #     Acknowledge(RequestWrappingReminder).With(RequestWrappingAck, "ackID"),
    # )

    adapter.start()
