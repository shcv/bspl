from adapter import Adapter
from protocheck import bspl
from configuration import config, prescription
import random
import threading

adapter = Adapter(prescription.roles['Doctor'], prescription, config)


@adapter.received(prescription.messages['Request'])
def request(message):
    print(message)

    treatment = {
        "Stomache ache": "Calcium carbonate",
        "Sneezing": "Diphenhydramine",
        "Cough": "Dextromethorphan",
        "Nausea": "Bismuth sub-salicylate",
        "Hemorrhage": "Vitamins",
        "Death": "Condolences",
    }

    payload = {
        'reqID': message.payload['reqID'],
        'details': message.payload['details'],
        'Rx': treatment[message.payload['details']]}
    adapter.send(payload, prescription.messages['Prescribe'])


if __name__ == '__main__':
    print("Starting Doctor...")
    adapter.start()
