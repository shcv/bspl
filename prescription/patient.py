from adapter import Adapter
from protocheck import bspl
from configuration import config, prescription
import random
import threading

adapter = Adapter(prescription.roles['Patient'], prescription, config)


def request_generator():
    reqID = 0
    symptoms = [
        "Stomache ache",
        "Sneezing",
        "Cough",
        "Nausea",
        "Hemorrhage",
        "Death",
    ]
    while(True):
        adapter.send({
            "reqID": reqID,
            "details": random.sample(symptoms, 1)[0],
        }, prescription.messages['Request'])
        reqID += 1


@adapter.received(prescription.messages['Filled'])
def filled(message):
    print(message)


if __name__ == "__main__":
    print("Starting Patient...")
    adapter.start()
    threading.Thread(target=request_generator).start()
