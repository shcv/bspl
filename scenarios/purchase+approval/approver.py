#!/usr/bin/env python3

from bspl.adapter import Adapter
from configuration import systems, agents
from Approval import Approve
import random

adapter = Adapter("Alice", systems, agents)


@adapter.enabled(Approve)
async def approve(msg):
    # approve half of requests randomly
    adapter.info(f"request: {msg}")
    if random.random() < 0.75:
        msg["approved"] = "True"
        adapter.info("approved")
        return msg
    else:
        adapter.info("denied")


if __name__ == "__main__":
    adapter.start()
