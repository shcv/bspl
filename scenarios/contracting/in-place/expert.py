#!/usr/bin/env python3

from bspl.adapter import Adapter
import asyncio
import logging

from configuration import config
import Contracting
from Contracting import Expert, Opine

adapter = Adapter(Expert, Contracting.protocol, config)
logger = logging.getLogger("expert")


@adapter.enabled(Opine)
async def make_opinion(msg):
    logger.info(f"asked for opinion: {msg}")
    opinion = "feasible" if msg["proposal"] > 20000 else "lowball"
    msg.bind(report=opinion)
    logger.info(f"reported: {msg}")
    return msg


if __name__ == "__main__":
    adapter.start()
