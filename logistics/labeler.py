from bungie import Adapter, Resend
from configuration import config, logistics
import uuid

adapter = Adapter(logistics.roles['Labeler'], logistics, config)


@adapter.reaction(logistics.messages['RequestLabel'])
def request_label(message):
    print(message)

    payload = {
        'orderID': message.payload['orderID'],
        'address': message.payload['address'],
        'label': str(uuid.uuid4()),
    }
    adapter.send(payload, logistics.messages['Labeled'])


RequestLabel = logistics.messages['RequestLabel']
Labeled = logistics.messages['Labeled']

if __name__ == '__main__':
    print("Starting Labeler...")
    adapter.add_policy(Resend(Labeled).upon.duplicate(RequestLabel))
    adapter.start()
