import random
import asyncio
import cProfile
from bspl import Adapter
from bspl.policies import Remind, Forward

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


completed = set()


if __name__ == "__main__":
    print("Starting Patient...")
    complaints = 10000

    @adapter.reaction(FilledRx, RetryFilledRx)
    async def filled(message):
        key = message["sID"]
        if key not in completed:
            print(f"completed: {len(completed)}")
            completed.add(key)
            if len(completed) == complaints:
                asyncio.get_running_loop().stop()  # record final results before stopping

    adapter.add_policies(
        Remind(Complaint)
        .With(Map)
        .after(1)
        .until.received(Copy)
        .Or.received(FilledRx)
        .received(RetryFilledRx),
        Forward(Copy)
        .to(Pharmacist)
        .after(1)
        .With(Map)
        .until.received(FilledRx)
        .Or.received(RetryFilledRx),
        when="every 0.1s",
    )
    adapter.start(
        complaint_generator(complaints),
    )
