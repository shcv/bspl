from bungie import Adapter
from bungie.emitter import TCPEmitter
from configuration import config, protocol, Want, WillPay, Buyer
import random

adapter = Adapter(Buyer,
                  protocol,
                  config,
                  emitter=TCPEmitter())


async def order_generator():
    for orderID in range(5):
        item = random.sample(['ball', 'bat', 'car', 'cat'], 1)[0]
        adapter.send({
            "ID": orderID,
            "item": item
        }, Want)
        adapter.send({
            "ID": orderID,
            "item": item,
            "price": random.randint(10, 100)
        }, WillPay)

if __name__ == '__main__':
    print("Starting Buyer...")
    adapter.start(order_generator())
