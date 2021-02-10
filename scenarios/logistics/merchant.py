from bungie import Adapter, Resend, Scheduler
from bungie.performance import perf_logger
from configuration import config, logistics
import random
import time
import datetime
import asyncio
import logging

RequestLabel = logistics.messages['RequestLabel']
RequestWrapping = logistics.messages['RequestWrapping']
Packed = logistics.messages['Packed']

adapter = Adapter(logistics.roles['Merchant'], logistics, config)
logger = logging.getLogger('merchant')
# logging.getLogger('bungie').setLevel(logging.DEBUG)

stats = {
    "init_keys": set(),
    "finished_keys": set(),
    "information": [0],
    "done": False
}


async def order_generator():
    for orderID in range(10000):
        adapter.send({
            "orderID": orderID,
            "address": random.sample(['Lancaster University', 'NCSU'], 1)[0]
        }, RequestLabel)
        for i in range(2):
            adapter.send({
                "orderID": orderID,
                "itemID": i,
                "item": random.sample(['ball', 'bat', 'plate', 'glass'], 1)[0]
            }, RequestWrapping)
        await asyncio.sleep(0)
    stats['done'] = True


@adapter.reaction(RequestWrapping)
async def requested(message):
    if message.duplicate:
        return
    stats['init_keys'].add(message.key)


@adapter.reaction(Packed)
async def packed(message):
    if message.duplicate:
        return
    stats['finished_keys'].add(message.key)


async def status_logger():
    start = datetime.datetime.now()
    while True:
        initiated = len(stats['init_keys'])
        completed = len(stats['finished_keys'])
        if not stats['done']:
            duration = datetime.datetime.now() - start
            rate = completed / duration.total_seconds()
        logger.info(
            f"initiated: {initiated}, completed: {completed}, duration: {duration}, rate: {rate}")
        logger.info(
            f"TX: {adapter.emitter.stats}")
        await asyncio.sleep(3)

if __name__ == '__main__':
    print("Starting Merchant...")
    adapter.load_policy_file('policies.yaml')
    adapter.start(order_generator(), perf_logger(3), status_logger())
