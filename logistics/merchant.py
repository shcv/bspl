from bungie import Adapter, Resend, Scheduler
from configuration import config, logistics
import random
import threading

RequestLabel = logistics.messages['RequestLabel']
RequestWrapping = logistics.messages['RequestWrapping']
Packed = logistics.messages['Packed']

adapter = Adapter(logistics.roles['Merchant'], logistics, config)


def order_generator():
    orderID = 0
    while(True):
        adapter.send({
            "orderID": orderID,
            "address": random.sample(['Lancaster University', 'NCSU'], 1)[0]
        }, RequestLabel)
        for i in range(random.randint(1, 4)):
            adapter.send({
                "orderID": orderID,
                "itemID": i,
                "item": random.sample(['ball', 'bat', 'plate', 'glass'], 1)[0]
            }, RequestWrapping)
        orderID += 1
        sleep(1)


@adapter.reaction(Packed)
def packed(message):
    print(message)


if __name__ == '__main__':
    print("Starting Merchant...")
    sched = Scheduler(rate=1)
    sched.add(Resend(RequestLabel, RequestWrapping).until.received(Packed))
    sched.start(adapter)
    adapter.start()
    threading.Thread(target=order_generator).start()
