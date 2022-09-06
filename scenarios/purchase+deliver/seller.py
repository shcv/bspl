#!/usr/bin/env python3

import random
from bspl.adapter import Adapter
from configuration import systems

from Purchase import Seller, RFQ, Quote, Buy, Reject
from Deliver import Sender, Send

import sys

adapter = Adapter(sys.argv[1], systems)


@adapter.enabled(Quote)
async def send_quote(msg):
    msg["price"] = random.randint(20, 100)
    adapter.info(f"quoting: {msg}")
    return msg


@adapter.reaction(Buy)
async def handle_buy(msg):
    m = Send(pID=msg["ID"], package=adapter.history.context(msg).bindings["item"])
    await adapter.send(m)


if __name__ == "__main__":
    adapter.start()
