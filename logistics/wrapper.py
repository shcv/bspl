from bungie import Adapter, Resend
from configuration import config, logistics

adapter = Adapter(logistics.roles['Wrapper'], logistics, config)


@adapter.reaction(logistics.messages['RequestWrapping'])
def request_wrapping(message, adapter):
    print(message)
    item = message.payload['item']

    payload = {
        'orderID': message.payload['orderID'],
        'itemID': message.payload['itemID'],
        'item': item,
        'wrapping': 'bubblewrap' if item in ['plate', 'glass'] else 'paper',
    }
    adapter.send(payload, logistics.messages['Wrapped'])


RequestWrapping = logistics.messages['RequestLabel']
Wrapped = logistics.messages['Wrapped']

if __name__ == '__main__':
    print("Starting Wrapper...")
    adapter.add_policy(Resend(Wrapped).upon.duplicate(RequestWrapping))
    adapter.start()
