from bungie import Adapter
from configuration import config, protocol, Want, WillPay, Buyer
import random

adapter = Adapter(Buyer,
                  protocol,
                  config)


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
    adapter.add_policies(
        'resend WillPay until acknowledged',
        when='every 0.5s')
    adapter.start(order_generator())
