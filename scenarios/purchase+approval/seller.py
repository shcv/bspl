#!/usr/bin/env python3

import random
from bspl.adapter import Adapter
from configuration import systems, agents

from Purchase import Seller, RFQ, Quote, Buy, Reject

import sys
import logging

# logging.getLogger("bspl").setLevel(logging.DEBUG)

adapter = Adapter(sys.argv[1], systems, agents)


@adapter.enabled(Quote)
async def send_quote(msg):
    msg["price"] = random.randint(20, 100)
    adapter.info(f"quoting: {msg}")
    return msg


@adapter.reaction(Buy)
async def handle_buy(msg):
    adapter.info(f"sold {msg}")


if __name__ == "__main__":
    adapter.start()
