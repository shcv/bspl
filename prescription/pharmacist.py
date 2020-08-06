from adapter import Adapter
from protocheck import bspl
from configuration import config, prescription
import random
import threading
import uuid

adapter = Adapter(prescription.roles['Pharmacist'], prescription, config)


@adapter.received(prescription.messages['Prescribe'])
def handle_prescription(message):
    print(message)

    payload = {
        "reqID": message.payload['reqID'],
        "Rx": message.payload['Rx'],
        "package": str(uuid.uuid4()),
    }
    adapter.send(payload, prescription.messages['Filled'])


if __name__ == '__main__':
    print("Starting Pharmacist agent...")
    adapter.start()
