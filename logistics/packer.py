from bungie import Adapter, Resend
from configuration import config, logistics

Labeled = logistics.messages['Labeled']
Wrapped = logistics.messages['Wrapped']
Packed = logistics.messages['Packed']

adapter = Adapter(logistics.roles['Packer'], logistics, config)


@adapter.reaction(Labeled)
def labeled(message, adapter):
    print(message)

    orderID = message.payload['orderID']

    packed = [m for m in message.enactment['messages']
              if m.payload.get('status')]
    unpacked = [m for m in message.enactment['messages']
                if 'itemID' in m.payload and
                not any(p.payload.get('itemID') == m.payload['itemID'] for p in packed)]
    for m in unpacked:
        payload = {
            'orderID': orderID,
            'itemID': m.payload['itemID'],
            'wrapping': m.payload['wrapping'],
            'label': message.payload['label'],
            'status': 'packed'
        }
        adapter.send(payload, Packed)


@adapter.reaction(Wrapped)
def wrapped(message, adapter):
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
        adapter.send(payload, Packed)


if __name__ == '__main__':
    print("Starting Packer...")
    adapter.add_policy(Resend(Packed).upon.duplicate(
        Labeled).Or.duplicate(Wrapped))
    adapter.start()
