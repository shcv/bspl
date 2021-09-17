from bungie import Adapter

from configuration import (
    config,
    treatment,
    Doctor,
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
    adapter.start()
