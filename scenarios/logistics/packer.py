import logging
from bungie import Adapter, Resend
from configuration import config, logistics
from bungie.performance import perf_logger

from Logistics import Packer, Labeled, Wrapped, Packed

adapter = Adapter(Packer, logistics, config)

logger = logging.getLogger("bungie")
# logger.setLevel(logging.DEBUG)


async def pack(message):
    for msg in Packed.match(**message.payload):
        msg.status = "packed"
        msg.send()


adapter.register_reactor(Labeled, pack)
adapter.register_reactor(Wrapped, pack)

if __name__ == "__main__":
    logger.info("Starting Packer...")
    adapter.load_policy_file("policies.yaml")
    adapter.start(perf_logger(3))
