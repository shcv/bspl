from bungie import Adapter, Resend, Scheduler
from bungie.statistics import stats_logger
from configuration import config, Map
import random
import time
import datetime
import asyncio
import logging

import Logistics
from Logistics import Merchant, RequestLabel, RequestWrapping, Packed

adapter = Adapter(Merchant, Logistics.protocol, config)
logger = logging.getLogger("merchant")
# logging.getLogger('bungie').setLevel(logging.DEBUG)

stats = {"init_keys": set(), "finished_keys": set(), "information": [0], "done": False}


async def order_generator():
    for orderID in range(10):
        adapter.send(
            {
                "orderID": orderID,
                "address": random.sample(["Lancaster University", "NCSU"], 1)[0],
            },
            RequestLabel,
        )
        for i in range(2):
            adapter.send(
                {
                    "orderID": orderID,
                    "itemID": i,
                    "item": random.sample(["ball", "bat", "plate", "glass"], 1)[0],
                },
                RequestWrapping,
            )
        await asyncio.sleep(0)
    stats["done"] = True


@adapter.reaction(RequestWrapping)
async def requested(message):
    stats["init_keys"].add(message.key)


@adapter.reaction(Packed)
async def packed(message):
    stats["finished_keys"].add(message.key)


async def status_logger():
    start = datetime.datetime.now()
    while True:
        initiated = len(stats["init_keys"])
        completed = len(stats["finished_keys"])
        if not stats["done"]:
            duration = datetime.datetime.now() - start
            rate = completed / duration.total_seconds()
        logger.info(
            f"initiated: {initiated}, completed: {completed}, duration: {duration}, rate: {rate}"
        )
        logger.info(f"TX: {adapter.emitter.stats}")
        await asyncio.sleep(3)


if __name__ == "__main__":
    print("Starting Merchant...")

    # resend policy
    # adapter.add_policies(
    #     Resend(RequestWrapping).With(Map).after(3).until.received(Packed),
    #     when="every 3s",
    # )

    # acknowledgment policy
    # adapter.add_policies(
    #     Resend(RequestWrapping).With(Map).after(3).until.acknowledged, when="every 3s"
    # )

    adapter.start(order_generator(), stats_logger(3), status_logger())
