from adapter import Adapter
from protocheck import bspl
from configuration import config, logistics
import random
import threading

adapter = Adapter(logistics.roles['Merchant'], logistics, config)


def order_generator():
    orderID = 0
    while(True):
        adapter.send({
            "orderID": orderID,
            "address": random.sample(['Lancaster University', 'NCSU'], 1)[0]
        }, logistics.messages['RequestLabel'])
        for i in range(random.randint(1, 4)):
            adapter.send({
                "orderID": orderID,
                "itemID": i,
                "item": random.sample(['ball', 'bat', 'plate', 'glass'], 1)[0]
            }, logistics.messages['RequestWrapping'])
        orderID += 1


@adapter.received(logistics.messages['Packed'])
def packed(message):
    print(message)


if __name__ == '__main__':
    print("Starting Merchant...")
    adapter.start()
    threading.Thread(target=order_generator).start()
