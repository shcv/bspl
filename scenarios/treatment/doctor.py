from bungie import Adapter
from bungie.policies import Forward, Remind

from configuration import (
    config,
    treatment,
    Doctor,
    Patient,
    Complaint,
    Prescription,
    Map,
    RetryComplaint,
)

adapter = Adapter(Doctor, treatment, config)

prescriptions = {
    "Stomach ache": "Calcium carbonate",
    "Sneezing": "Diphenhydramine",
    "Cough": "Dextromethorphan",
    "Nausea": "Bismuth sub-salicylate",
    "Hemorrhage": "Vitamins",
    "Death": "Condolences",
}


@adapter.reaction(Complaint, RetryComplaint)
async def request(message):
    msg = Prescription(
        sID=message["sID"],
        symptom=message["symptom"],
        Rx=prescriptions[message["symptom"]],
    )

    adapter.send(msg)


if __name__ == "__main__":
    print("Starting Doctor...")
    adapter.emitter.loss = 0.5
    print(f"Doctor's loss rate set to: {adapter.emitter.loss}")
    p1 = (
        Forward(Prescription)
        .to(Patient)
        .With(Map)
        .upon.observed(Prescription, RetryComplaint)
    )
    p2 = Remind(Prescription).With(Map).upon.received(RetryComplaint)
    adapter.add_policies(p1, p2)
    adapter.start()
