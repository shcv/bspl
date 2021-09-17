import random
import asyncio
import cProfile
from bungie import Adapter

from configuration import (
    config,
    treatment,
    Patient,
    Doctor,
    Pharmacist,
    Complaint,
    Map,
    FilledRx,
    RetryFilledRx,
    Copy,
)

adapter = Adapter(Patient, treatment, config)


async def complaint_generator(complaints=1):
    sID = 0
    symptom = [
        "Sneezing",
        "Cough",
        "Stomach ache",
        "Nausea",
        "Hemorrhage",
        "Death",
    ]
    while sID < complaints:
        # construct mesage
        msg = Complaint(sID=sID, symptom=random.sample(symptom, 1)[0])

        # send message
        adapter.send(msg)

        sID += 1
        await asyncio.sleep(0)


if __name__ == "__main__":
    print("Starting Patient...")
    # cProfile.run("adapter.start(complaint_generator(1000))")
    adapter.start(complaint_generator())
