from bungie import Adapter
from configuration import (
    config,
    treatment,
    Pharmacist,
    Prescription,
    FilledRx,
    RetryPrescription,
    ForwardPrescription,
)

adapter = Adapter(Pharmacist, treatment, config)


@adapter.reaction(Prescription, RetryPrescription, ForwardPrescription)
async def handle_prescription(message):
    msg = FilledRx(sID=message["sID"], Rx=message["Rx"], done=True)
    adapter.send(msg)


if __name__ == "__main__":
    print("Starting Pharmacist agent...")
    adapter.start()
