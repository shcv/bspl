from bungie import Adapter
from configuration import config, logistics, Wrapped, RequestWrapping
import logging

logger = logging.getLogger("wrapper")
# logging.getLogger('bungie').setLevel(logging.DEBUG)

adapter = Adapter(logistics.roles["Wrapper"], logistics, config)


@adapter.enabled(Wrapped)
async def wrap(msg):
    item = msg.payload["item"]
    msg.bind(wrapping="bubblewrap" if item in ["plate", "glass"] else "paper")
    return msg


if __name__ == "__main__":
    logger.info("Starting Wrapper...")

    # acknowledge Complain
    # adapter.add_policies(
    #     Acknowledge(RequestWrapping).Map(Map),
    #     Acknowledge(RequestWrappingReminder).With(RequestWrappingAck, "ackID"),
    # )

    adapter.start()
