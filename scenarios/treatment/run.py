#!/usr/bin/env python3

import multiprocessing as mp
from patient import adapter as patient, complaint_generator
from doctor import adapter as doctor
from pharmacist import adapter as pharmacist
from configuration import *

from bungie.policies import Remind, Forward


def doctor_proc():
    doctor.emitter.loss = 0.5
    # add checkpoint policy
    p1 = (
        Forward(Prescription)
        .to(Patient)
        .With(Map)
        .upon.observed(Prescription, RetryComplaint)
    )
    p2 = Remind(Prescription).With(Map).upon.received(RetryComplaint)
    doctor.add_policies(p1, p2)
    doctor.start()


def pharmacist_proc():
    # add checkpoint policy
    policy = (
        Remind(FilledRx).With(Map).upon.received(RetryPrescription, ForwardPrescription)
    )
    pharmacist.add_policies(policy)
    pharmacist.start()


if __name__ == "__main__":
    d = mp.Process(target=doctor_proc)
    ph = mp.Process(target=pharmacist_proc)

    d.start()
    ph.start()

    patient.add_policies(
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
        when="every 1s",
    )

    patient.start(complaint_generator(1000))
    d.terminate()
    ph.terminate()
