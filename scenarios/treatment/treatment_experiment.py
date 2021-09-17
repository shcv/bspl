#!/usr/bin/env python3

import asyncio
import fire
import multiprocessing as mp
import time
import logging
import signal
import sys
import pandas as pd

import mandrake
from mandrake import statistics
from mandrake.policies import Remind, Forward
from spearmint import Experiment

# local files
from patient import adapter as patient, complaint_generator
from doctor import adapter as doctor
from pharmacist import adapter as pharmacist
from configuration import *

experiment = Experiment(
    name="treatment",
    parameters={
        "iteration": range(5),
        "max-time": [30],
        "complaints": [1000],
        "recovery": (
            "none",
            "retry",
            "checkpoint",
        ),
        "loss": [
            # patient, doctor, pharmacist
            # baseline
            (0, 0, 0),
            # only patient
            (0.01, 0, 0),
            (0.1, 0, 0),
            (0.5, 0, 0),
            # only doctor
            (0, 0.01, 0),
            (0, 0.1, 0),
            (0, 0.5, 0),
            # all three
            (0.01, 0.01, 0.01),
            (0.1, 0.1, 0.1),
            (0.5, 0.5, 0.5),
        ],
    },
)


@experiment.preprocess
def listify(exp):
    for k in exp.keys:
        k["loss"] = tuple(k["loss"])


def split_losses(exp):
    def fix(obj):
        if "loss" in obj:
            obj["patient-loss"] = obj["loss"][0]
            obj["doctor-loss"] = obj["loss"][1]
            obj["pharmacist-loss"] = obj["loss"][2]
            del obj["loss"]

    for k in exp.keys:
        fix(k)


def patient_proc(parameters, queue):
    # patient.logger.setLevel(logging.DEBUG)
    # mandrake.scheduler.logger.setLevel(logging.DEBUG)
    # mandrake.policies.logger.setLevel(logging.DEBUG)
    patient.emitter.loss = parameters["loss"][0]

    statistics.stats["completed"] = 0

    if parameters["recovery"] == "retry":
        # add retry policies
        patient.add_policies(
            Remind(Complaint)
            .With(Map)
            .after(1)
            .until.received(FilledRx)
            .Or.received(RetryFilledRx),
            when="every 1s",
        )
    elif parameters["recovery"] == "checkpoint":
        # add checkpoint policy
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

    completed = set()

    def stop():
        statistics.stats["packets"] = patient.emitter.stats["packets"]
        stats = statistics.stats.copy()
        [stats.pop(k) for k in ("observations", "receptions")]
        queue.put(stats)
        # no need to continue once steady state is reached, if there is no recovery
        asyncio.get_running_loop().stop()

    def check_status(prev={"completed": None}):
        if (
            parameters["recovery"] == "none"
            and statistics.stats["completed"] == prev["completed"]
        ):
            stop()
        prev.update(statistics.stats)

    # async def count_message(msg):
    #     statistics.increment(msg.schema.name)

    # for s in [
    #     Copy,
    #     ForwardPrescription,
    #     RetryComplaint,
    #     Complaint,
    #     RetryFilledRx,
    #     FilledRx,
    # ]:
    #     patient.register_reactor(s, count_message)

    @patient.reaction(FilledRx, RetryFilledRx)
    async def filled(message):
        key = message["sID"]
        if key not in completed:
            completed.add(key)
            statistics.increment("completed")
            if statistics.stats["completed"] == parameters["complaints"]:
                stop()  # record final results before stopping

    async def timeout(max_time):
        start = time.time()
        while True:
            check_status()  # check for steady-state on non-recovery runs
            now = time.time()
            if now - start > max_time:
                stop()
            await asyncio.sleep(0.1)

    patient.start(
        complaint_generator(parameters["complaints"]), timeout(parameters["max-time"])
    )


def doctor_proc(parameters):
    # doctor.logger.setLevel(logging.DEBUG)
    doctor.emitter.loss = parameters["loss"][1]
    if parameters["recovery"] == "retry":
        # add retry policies
        doctor.add_policies(
            Remind(Prescription).With(Map).upon.received(RetryComplaint),
        )
    elif parameters["recovery"] == "checkpoint":
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


def pharmacist_proc(parameters):
    # pharmacist.logger.setLevel(logging.DEBUG)
    pharmacist.emitter.loss = parameters["loss"][2]
    if parameters["recovery"] == "retry":
        # add retry policies
        pharmacist.add_policies(
            Remind(FilledRx).With(Map).upon.received(RetryPrescription)
        )
    elif parameters["recovery"] == "checkpoint":
        # add checkpoint policy
        policy = (
            Remind(FilledRx)
            .With(Map)
            .upon.received(RetryPrescription, ForwardPrescription)
        )
        pharmacist.add_policies(policy)

    pharmacist.start()


@experiment.action
def main(**kwargs):
    queue = mp.Queue()

    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

    p = mp.Process(target=patient_proc, args=(kwargs, queue))
    d = mp.Process(target=doctor_proc, args=(kwargs,))
    ph = mp.Process(target=pharmacist_proc, args=(kwargs,))

    d.start()
    ph.start()
    p.start()  # start patient last so the other agents can start listening first

    signal.signal(signal.SIGINT, original_sigint_handler)

    while p.is_alive():
        try:
            result = queue.get(timeout=0.1)
            yield result
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            pass

    d.terminate()
    ph.terminate()
    d.join()
    ph.join()


@experiment.postprocess
def post(df):
    df["duration"] = pd.to_numeric(df["duration"])
    df["rate"] = df["completed"] / df["duration"]

    return df


# run patient until max-time or number of complaints; return results from patient
# terminate doctor and pharmacist


if __name__ == "__main__":
    fire.Fire(experiment)
    # experiment.run()
