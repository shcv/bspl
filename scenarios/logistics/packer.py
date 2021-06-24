import logging
from bungie import Adapter, Remind
from configuration import config, logistics
from bungie.statistics import stats_logger

from Logistics import Packer, Packed

adapter = Adapter(Packer, logistics, config)

logger = logging.getLogger("bungie")
# logger.setLevel(logging.DEBUG)


@adapter.enabled(Packed)
async def pack(msg):
    msg["status"] = "packed"
    print(msg)
    return msg


if __name__ == "__main__":
    logger.info("Starting Packer...")
    # adapter.load_policy_file("policies.yaml")
    adapter.start(stats_logger(3))
