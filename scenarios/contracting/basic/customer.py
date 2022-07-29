#!/usr/bin/env python3

from bspl.adapter import Adapter, Scheduler
from configuration import config
import asyncio
import logging

import Contracting
from Contracting import (
    Customer,
    Invite,
    RequestApproval,
    RequestOpinion,
    Allow,
    Opine,
    Accept,
    Reject,
)

adapter = Adapter(Customer, Contracting.protocol, config)
logger = logging.getLogger("government")


async def main():
    invitations = [Invite(contractID=1, bidID=i, spec="mobile app") for i in range(10)]
    logger.info(f"Inviting bids: {invitations}")
    await adapter.send(*invitations)


@adapter.decision
async def request_handler(enabled):
    requests = set()
    for m in enabled.messages:
        if m.schema is RequestApproval:
            requests.add(m.bind(req=True))
        elif m.schema is RequestOpinion:
            requests.add(m.bind(req2=True))
    return requests


@adapter.schedule_decision("1s")
async def response_handler(enabled):
    results = []
    for contractID in set(m["contractID"] for m in enabled.messages):
        messages = [m for m in enabled.messages if m["contractID"] == contractID]
        accepts = [m for m in messages if m.schema == Accept]
        rejects = [m for m in messages if m.schema == Reject]
        if len(rejects) >= 3 and len(accepts):
            # a bid is only acceptable if accountant says we can afford it
            feasible = [m for m in accepts if m["report"] == "feasible"]
            selection = None
            reason = None
            if len(feasible):
                # want the lowest of the feasible bids
                selection = min(m["proposal"] for m in feasible)
            else:
                # want the highest of the lowball options
                selection = max(m["proposal"] for m in accepts)
            winner = next(
                m.bind(acceptance=True, closed=True)
                for m in accepts
                if m["proposal"] == selection
            )
            losers = [
                m.bind(
                    rejection="lowball" if m["proposal"] < selection else "outbid",
                    closed=True,
                )
                for m in rejects
                if m["bidID"] is not winner["bidID"]
            ]
            results.extend([winner, *losers])
    logger.debug(f"results: {results}")
    return results


@adapter.reaction(Allow)
async def allow(msg):
    print(msg)


@adapter.reaction(Opine)
async def opine(msg):
    print(msg)


if __name__ == "__main__":
    adapter.start(main())
