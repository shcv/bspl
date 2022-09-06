#!/usr/bin/env python3

import uuid, random, asyncio
from bspl.adapter import Adapter
from configuration import systems
from itertools import combinations

import Purchase
from Purchase import Buyer, RFQ, Quote, Buy, Reject
from Deliver import Ship

adapter = Adapter("B", systems, in_place=True)

asked = set()


def subsets(col):
    for r in range(len(col)):
        yield from combinations(col, r)


@adapter.schedule_decision("0s")
async def start(enabled):
    global asked
    for item in ["ball", "bat", "glove"]:
        ID = str(uuid.uuid4())
        for m in enabled.messages(RFQ):
            if (item, m.recipient) not in asked:
                m.bind(ID=ID, item=item)
                adapter.debug(f"asking: {m.instances}")
                asked.add((item, m.recipient))


@adapter.schedule_decision("1s")
async def select_gifts(enabled):
    buys = list(enabled.messages(Buy))
    if not buys:
        return
    best_buys = {}
    # get all of the distinct active IDs
    IDs = set(b["ID"] for b in buys)
    # compute the cheapest option for each item
    for ID in IDs:
        best_buys[ID] = min(enabled.messages(Buy, ID=ID), key=lambda m: m["price"])
    costs = {}
    # compute the costs of each combination of items
    for combo in subsets(best_buys):
        costs[combo] = sum(best_buys[ID]["price"] for ID in combo)
    # list all combos less than the budget
    affordable = [combo for combo in costs if costs[combo] < 100]
    # select the best combo as the least expensive one that includes the most items
    best = max(sorted(affordable, key=lambda c: costs[c]), key=lambda c: len(c))
    print(f"best combo: {best}, cost: {costs[best]}")

    # buy the best items
    for ID in best:
        b = best_buys[ID]
        b.bind(payment=b["price"], accept=True, done=True)
        adapter.info(f"buying; {b}")

    # reject any other items
    for ID in IDs:
        for m in enabled.messages(Reject, ID=ID):
            if not ID in best or m.system != best_buys[ID].system:
                m.bind(reject=True, done=True)
                adapter.info(f"rejecting; {m}")


@adapter.reaction(Ship)
async def receive(msg):
    adapter.info(f"received: {msg}")


if __name__ == "__main__":
    adapter.start()
