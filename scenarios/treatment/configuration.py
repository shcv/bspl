from protocheck import bspl

treatment = bspl.load_file("treatment.bspl").export("Treatment")
from Treatment import *

with open("/proc/self/cgroup", "r") as cgroups:
    in_docker = "docker" in cgroups.read()

if in_docker:
    config = {
        Patient: ("patient", 8000),
        Doctor: ("doctor", 8000),
        Pharmacist: ("pharmacist", 8000),
    }
else:
    # use different ports for each agent
    config = {
        Patient: ("0.0.0.0", 8000),
        Doctor: ("0.0.0.0", 8001),
        Pharmacist: ("0.0.0.0", 8002),
    }

Map = {
    "reminders": {
        Complaint: (RetryComplaint, "rcID"),
        Prescription: (RetryPrescription, "rpID"),
        FilledRx: (RetryFilledRx, "rfID"),
    },
    "forwards": {
        Prescription: (Copy, "cpID"),
        Copy: (ForwardPrescription, "fpID"),
    },
}
