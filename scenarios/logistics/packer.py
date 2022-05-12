import logging
from bspl import Adapter, Remind
from configuration import config, logistics
from bspl.statistics import stats_logger

from Logistics import Packer, Packed

adapter = Adapter(Packer, logistics, config)

logger = logging.getLogger("bspl")
# logger.setLevel(logging.DEBUG)


@adapter.enabled(Packed)
async def pack(msg):
    msg["status"] = "packed"
    return msg


if __name__ == "__main__":
    logger.info("Starting Packer...")
    adapter.start()
