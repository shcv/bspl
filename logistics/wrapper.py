from adapter import Adapter
from protocheck import bspl
from configuration import config, logistics

adapter = Adapter(logistics.roles['Wrapper'], logistics, config)


@adapter.received(logistics.messages['RequestWrapping'])
def request_wrapping(message):
    print(message)
    item = message.payload['item']

    payload = {
        'orderID': message.payload['orderID'],
        'itemID': message.payload['itemID'],
        'item': item,
        'wrapping': 'bubblewrap' if item in ['plate', 'glass'] else 'paper',
    }
    adapter.send(payload, logistics.messages['Wrapped'])


if __name__ == '__main__':
    print("Starting Wrapper...")
    adapter.start()
