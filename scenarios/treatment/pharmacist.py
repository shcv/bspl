from bspl import Adapter
from bspl.policies import Remind
from configuration import (
    config,
    Map,
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
    policy = (
        Remind(FilledRx).With(Map).upon.received(RetryPrescription, ForwardPrescription)
    )
    adapter.add_policies(policy)
    adapter.start()
