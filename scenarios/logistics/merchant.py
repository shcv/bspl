from bungie import Adapter, Resend, Scheduler
from configuration import config, logistics
import random
import time
import datetime

RequestLabel = logistics.messages['RequestLabel']
RequestWrapping = logistics.messages['RequestWrapping']
Packed = logistics.messages['Packed']

adapter = Adapter(logistics.roles['Merchant'], logistics, config)


async def order_generator():
    for orderID in range(10):
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


init_keys = set()
finished_keys = set()


@adapter.reaction(RequestWrapping)
async def requested(message, enactment, adapter):
    init_keys.add(message.key)
    with open("requested-log", 'a') as file:
        file.write("{} {} {}\n".format(
            len(init_keys), message.key, str(datetime.datetime.now())))


@adapter.reaction(Packed)
async def packed(message, enactment, adapter):
    if message.duplicate:
        return
    finished_keys.add(message.key)
    with open("packed-log", 'a') as file:
        file.write("{} {} {}\n".format(
            len(finished_keys), message.key, str(datetime.datetime.now())))


if __name__ == '__main__':
    print("Starting Merchant...")
    adapter.load_policy_file('policies.yaml')
    adapter.start(order_generator())
