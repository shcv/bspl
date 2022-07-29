#!/usr/bin/env python3

from bspl.adapter import Adapter
import asyncio
import logging

from configuration import config
import Contracting
from Contracting import Accountant, Allow

adapter = Adapter(Accountant, Contracting.protocol, config)
logger = logging.getLogger("accountant")


@adapter.enabled(Allow)
async def allow(msg):
    logger.info(f"asked to approve: {msg}")
    if msg["proposal"] < 90000:
        msg.bind(approval=True)
        logger.info(f"approved: {msg}")
        return msg
    # how to reject message permanently?


if __name__ == "__main__":
    adapter.start()
