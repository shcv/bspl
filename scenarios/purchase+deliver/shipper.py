#!/usr/bin/env python3

from bspl.adapter import Adapter
from configuration import systems
from Deliver import Shipper, Ship

adapter = Adapter("Sh", systems)


@adapter.enabled(Ship)
async def ship(msg):
    msg["delivered"] = "delivered"
    return msg


if __name__ == "__main__":
    adapter.start()
