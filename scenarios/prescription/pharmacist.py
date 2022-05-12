import uuid
from bspl import Adapter
from configuration import config, prescription, Pharmacist, Prescribe, Filled

adapter = Adapter(Pharmacist, prescription, config)


@adapter.reaction(Prescribe)
async def handle_prescription(message):
    print(message)

    msg = Filled(cID=message.cID, Rx=message.Rx, package=str(uuid.uuid4()))
    adapter.send(msg)


if __name__ == "__main__":
    print("Starting Pharmacist agent...")
    adapter.start()
