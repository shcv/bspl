#!/usr/bin/env python3

import uuid, random, asyncio
from bspl.adapter import Adapter
from configuration import systems, agents
from itertools import combinations
from bspl.adapter.event import InitEvent
import aiocron

import Purchase
from Purchase import Buyer, Seller, RFQ, Quote, Buy, Reject
from Approval import Ask, Approve

adapter = Adapter("Bob", systems, agents, in_place=True)


def subsets(col):
    for r in range(len(col)):
        yield from combinations(col, r)


@adapter.decision(event=InitEvent)
async def start(enabled):
    for item in ["ball", "bat", "glove"]:
        ID = str(uuid.uuid4())
        for m in enabled.messages(RFQ):
            m.bind(ID=ID, item=item)
            adapter.info(
                f"requesting quote for {item} from {systems[m.system]['roles'][Seller]}"
            )


@adapter.enabled(Buy)
async def ask_approval(buy):
    # adapter.info(f"asking for approval for {buy}")
    ask = next(adapter.enabled_messages.messages(Ask), None)  # should be exactly one
    inst = ask.bind(aID=str(uuid.uuid4()), request=buy.payload)
    ask.instances.clear()
    return inst


@adapter.decision(event="select")
async def select_gifts(enabled):
    buys = list(enabled.messages(Buy))
    if not buys:
        return
    best_buys = {}
    # get all of the distinct active IDs
    IDs = set(b["ID"] for b in buys)
    approvals = list(
        adapter.history.messages(Approve, request=lambda r: r["ID"] in IDs)
    )
    # match on ID and price
    approved_buys = {
        b
        for b in buys
        for a in approvals
        if b["ID"] == a["request"]["ID"] and b["price"] == a["request"]["price"]
    }
    # compute the cheapest option for each item
    for ID in IDs:
        bs = [b for b in approved_buys if b["ID"] == ID]
        if not bs:
            continue
        best_buys[ID] = min(bs, key=lambda m: m["price"])
    costs = {}
    # compute the costs of each combination of items
    for combo in subsets(best_buys):
        costs[combo] = sum(best_buys[ID]["price"] for ID in combo)
    # list all combos less than the budget
    affordable = [combo for combo in costs if costs[combo] < 100]
    # select the best combo as the least expensive one that includes the most items
    best = max(sorted(affordable, key=lambda c: costs[c]), key=lambda c: len(c))
    adapter.info(f"best combo: {best}, cost: {costs[best]}")

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


async def trigger_selection():
    await asyncio.sleep(2)
    await adapter.signal("select")


if __name__ == "__main__":
    adapter.start(trigger_selection())
