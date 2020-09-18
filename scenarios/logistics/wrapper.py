from bungie import Adapter, Resend
from configuration import config, logistics

adapter = Adapter(logistics.roles['Wrapper'], logistics, config)
RequestWrapping = logistics.messages['RequestWrapping']
Wrapped = logistics.messages['Wrapped']


@adapter.reaction(RequestWrapping)
async def request_wrapping(message, enactment, adapter):
    if message.duplicate:
        return
    item = message.payload['item']

    payload = {
        'orderID': message.payload['orderID'],
        'itemID': message.payload['itemID'],
        'item': item,
        'wrapping': 'bubblewrap' if item in ['plate', 'glass'] else 'paper',
    }
    adapter.send(payload, Wrapped)


if __name__ == '__main__':
    print("Starting Wrapper...")
    adapter.load_policy_file('policies.yaml')
    adapter.start()
