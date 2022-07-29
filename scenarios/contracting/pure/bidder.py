#!/usr/bin/env python3

from bspl.adapter import Adapter
import random
import asyncio
import logging

from configuration import config
import Contracting
from Contracting import Bidder, Tender, Accept, Reject

adapter = Adapter(Bidder, Contracting.protocol, config)
logger = logging.getLogger("bidder")


@adapter.enabled(Tender)
async def make_bid(msg):
    msg.bind(proposal=random.randint(1000, 100000))
    return msg


@adapter.reaction(Accept)
async def won(msg):
    logger.info(f"Bid {msg['bidID']} won with proposal {msg['proposal']}")


@adapter.reaction(Reject)
async def lost(msg):
    logger.info(
        f"Bid {msg['bidID']} lost with proposal {msg['proposal']}; reason: {msg['rejection']}"
    )


if __name__ == "__main__":
    adapter.start()
