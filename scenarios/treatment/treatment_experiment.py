#!/usr/bin/env python3

import asyncio
import fire
import multiprocessing as mp
import time
import logging
import signal
import sys
import pandas as pd

import bspl
from bspl import statistics
from bspl.policies import Remind, Forward
from spearmint import Experiment

# local files
from patient import adapter as patient, complaint_generator
from doctor import adapter as doctor
from pharmacist import adapter as pharmacist
from configuration import *

idx = pd.IndexSlice

experiment = Experiment(
    name="treatment",
    parameters={
        "max-time": [30],
        "complaints": [1000],
        "lossy": [
            [],
            ["patient"],
            ["doctor"],
            ["pharmacist"],
            ["doctor", "pharmacist"],
            ["patient", "doctor", "pharmacist"],
        ],
        "loss-rate": [0.01, 0.05, 0.25],
        "recovery": (
            "none",
            "retry",
            "checkpoint",
        ),
        "iteration": range(5),
    },
)


@experiment.preprocess
def listify(exp):
    for k in exp.keys:
        k.pop("max-time")
        k.pop("complaints")
        k["lossy"] = tuple(k["lossy"])
        k["loss-rate"] = float(k["loss-rate"])


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
    # bspl.scheduler.logger.setLevel(logging.DEBUG)
    # bspl.policies.logger.setLevel(logging.DEBUG)
    if "patient" in parameters["lossy"]:
        patient.emitter.loss = parameters["loss-rate"]

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
    if "doctor" in parameters["lossy"]:
        doctor.emitter.loss = parameters["loss-rate"]
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
    if "pharmacist" in parameters["lossy"]:
        pharmacist.emitter.loss = parameters["loss-rate"]
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
    df = df.drop(columns=["duration"])

    return df


@experiment.postprocess
def results(df):
    avg = df.groupby(["lossy", "loss-rate", "recovery"]).mean()
    std = df.groupby(["lossy", "loss-rate", "recovery"]).std()
    columns = [c for c in avg.columns]
    print(columns)
    for col in columns:
        avg[col + "-std"] = std[col]
    experiment.columns = columns
    return avg


@experiment.command("write-data")
def write_data():
    for case in experiment.parameters["lossy"]:
        casename = "_".join(case)
        for col in experiment.columns:
            for recovery in ["none", "retry", "checkpoint"]:
                filename = "_".join([col] + case + [recovery]) + ".dat"
                print(f"Writing data to {filename} with fields: loss, {col}, err")
                experiment.frame.loc[tuple(case)].xs(recovery, level="recovery")[
                    [col, col + "-std"]
                ].to_string(
                    "data/" + filename, sparsify=False, header=False, index_names=False
                )
    return experiment


class Figure:
    def __init__(self, caption, label):
        self.subfigures = []
        self.caption = caption
        self.label = label

    def add(self, sub):
        self.subfigures.append(sub)

    def __str__(self):
        nl = "\n"
        return f"""\
\\begin{{figure}}[ht]
\\centering
{nl.join(str(s) for s in self.subfigures)}
\\caption{{{self.caption}}}
\\label{{fig:{self.label}}}
\\end{{figure}}

"""


class Subfigure:
    def __init__(self, context, case, caption, xlabel=None, ylabel=None, legend=None):
        self.case = case
        self.caption = caption
        self.xlabel = f"xlabel = {{loss rate}}," if xlabel else ""
        self.ylabel = f"ylabel = {{{ylabel}}}," if ylabel else ""
        self.plots = []
        self.name = context + "-" + "-".join(case or ["no-loss"]) + "-subfig.tex"
        self.legend = f"\\legend{{{','.join(legend)}}}" if legend else ""

    def add(self, *plots):
        self.plots.extend(plots)

    def write(self, path):
        with open(path + "/" + self.name, "w") as f:
            f.write(
                f"""\
\\begin{{tikzpicture}}
\\begin{{axis}}[{self.xlabel} {self.ylabel}
  width = 4cm, height = 4cm,
  legend style = {{at={{(1,1.1)}},anchor=south east}}
]
{"".join(str(p) for p in self.plots)}\
{{{self.legend}}}
\\end{{axis}}
\\end{{tikzpicture}}
"""
            )

    def __str__(self):
        inclusion = f"\\subcaptionbox{{{self.caption}}}[0.3\\textwidth]{{\includegraphics{{JAAMAS/figs/{self.name}}}}}"
        if self.ylabel:
            inclusion += "\n\hspace{.5em}"
        return inclusion


def plot(filename):
    return f"\\addplot table[x index=0,y index=1,y error index=2, header=false] {{JAAMAS/data/{filename}}};\n"


case_map = {
    tuple(): {"caption": "No Loss", "ylabel": True},
    ("patient",): {"caption": "Patient Only"},
    ("doctor",): {"caption": "Doctor Only", "legend": True},
    ("pharmacist",): {"caption": "Pharmacist Only", "ylabel": True},
    ("doctor", "pharmacist"): {"caption": "Docter + Pharmacist"},
    ("patient", "doctor", "pharmacist"): {
        "caption": "All",
    },
}

captions = {
    "completed": """Total enactments completed.
Each subfigure represents a different loss configuration, with the lines representing the recovery policies.
In this figure, a line is also given for the absence of a recovery policy, to show the cumulative effect of the loss rate.
Subfigure (a) has no loss, (b-d) have one lossy agent, (e) has both doctor and pharmacist lossy, and in (f) all agents are equally lossy.
The Y-axes show the number of enactments completed by the timeout, which is set to be 30 seconds.
The X-axes are the three different loss rates tested: 0.01, 0.05, and 0.25.""",
    "emissions": """Messages emitted.
Each subfigure represents a different loss configuration, with the lines representing the two recovery policies.
Subfigure (a) has no loss, (b-d) have one lossy agent, (e) has both doctor and pharmacist lossy, and in (f) all agents are equally lossy.
The Y-axes show the number of messages emitted by \\rname{Patient}.
The X-axes are the three different loss rates tested: 0.01, 0.05, and 0.25.""",
    "packets": """Total packets sent.
Each subfigure represents a different loss configuration, with the lines representing the two recovery policies.
Subfigure (a) has no loss, (b-d) have one lossy agent, (e) has both doctor and pharmacist lossy, and in (f) all agents are equally lossy.
The Y-axes show the number of UDP packets sent by \\rname{Patient}.
The X-axes are the three different loss rates tested: 0.01, 0.05, and 0.25.""",
    "rate": """Rate of completion (enactments/second).
Each subfigure represents a different loss configuration, with the lines representing the two recovery policies.
Subfigure (a) has no loss, (b-d) have one lossy agent, (e) has both doctor and pharmacist lossy, and in (f) all agents are equally lossy.
The Y-axes show the number of enactments completed (by observing \mname{FilledRx} or one of its reminders) divided by the duration of the iteration.
The X-axes are the three different loss rates tested: 0.01, 0.05, and 0.25.""",
}


@experiment.command("figure")
def figures():
    columns = [c for c in experiment.columns]
    with open(f"figs/figures.tex", "w") as f:
        for col in columns:
            fig = Figure(captions[col], col)
            for case in experiment.parameters["lossy"]:
                casename = "_".join(case)
                ylabel = (
                    col.capitalize() if case_map[tuple(case)].get("ylabel") else None
                )
                legend = ["None", "Retry", "Checkpoint"]
                if col != "completed":
                    legend = legend[1:]
                subfig = Subfigure(
                    col,
                    tuple(case),
                    case_map[tuple(case)]["caption"],
                    True,
                    ylabel,
                    legend if case_map[tuple(case)].get("legend") else None,
                )
                for recovery in ["none", "retry", "checkpoint"]:
                    if not (col != "completed" and recovery == "none"):
                        filename = "_".join([col] + case + [recovery]) + ".dat"
                        subfig.add(plot(filename))
                subfig.write("figs")
                fig.add(subfig)
            f.write(str(fig))


# run patient until max-time or number of complaints; return results from patient
# terminate doctor and pharmacist


if __name__ == "__main__":
    fire.Fire(experiment)
    # experiment.run()
