from adapter import Adapter
from protocheck import bspl
from configuration import config, logistics

adapter = Adapter(logistics.roles['Packer'], logistics, config)


@adapter.received(logistics.messages['Labeled'])
def labeled(message):
    print(message)

    orderID = message.payload['orderID']

    packed = [m for m in message.enactment['messages']
              if m.payload.get('status')]
    unpacked = [m for m in message.enactment['messages']
                if 'itemID' in m.payload and
                not any(p.payload.get('itemID') == m['itemID'] for p in packed)]
    for m in unpacked:
        payload = {
            'orderID': orderID,
            'itemID': m.payload['itemID'],
            'wrapping': m.payload['wrapping'],
            'label': message.payload['label'],
            'status': 'packed'
        }
        adapter.send(payload, logistics.messages['Packed'])


@adapter.received(logistics.messages['Wrapped'])
def wrapped(message):
    print(message)
    labeled_msg = next(
        (m for m in message.enactment['messages'] if m.payload.get("label")), None)

    if labeled_msg:
        payload = {
            'orderID': message.payload['orderID'],
            'itemID': message.payload['itemID'],
            'wrapping': message.payload['wrapping'],
            'label': labeled_msg.payload['label'],
            'status': 'packed'
        }
        adapter.send(payload, logistics.messages['Packed'])


if __name__ == '__main__':
    print("Starting Packer...")
    adapter.start()
