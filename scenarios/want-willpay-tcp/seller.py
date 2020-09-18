from bungie import Adapter
from bungie.receiver import TCPReceiver
from configuration import config, protocol, Want, WillPay, Seller
import random
import logging

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger('seller')

adapter = Adapter(Seller,
                  protocol,
                  config,
                  receiver=TCPReceiver(config[Seller]))

Want = protocol.messages['Want']
WillPay = protocol.messages['WillPay']


@adapter.reaction(Want)
async def want(msg, enactment, adapter):
    logging.info(f"Buyer wants: {msg.payload['item']}")


@adapter.reaction(WillPay)
async def want(msg, enactment, adapter):
    logging.info(
        f"Buyer is willing to pay ${msg.payload['price']} for {msg.payload['item']}")


if __name__ == '__main__':
    print("Starting Seller...")
    adapter.start()
