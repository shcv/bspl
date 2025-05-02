"""
Implementation of the CounterParty agent for the BilateralAgreement protocol.
"""

import asyncio
import logging
from bspl.adapter import Adapter
from configuration import agents, systems
from BilateralAgreement import (
    CounterParty,
    Request,
    Propose,
    Propose2,
    Accept,
    Reject,
    Execute,
    Ack,
    Withdraw,
)

# Create the CounterParty adapter
adapter = Adapter("counterparty", systems, agents)

# Simple counter for IDs
counter = 0

# Request types
REQUEST_TYPES = ["product", "service", "partner", "license"]


async def initiate_requests():
    """Send requests for agreements."""
    global counter

    for i in range(2):  # Start with 2 requests
        counter += 1
        ID = f"counter-{counter}"
        request_type = REQUEST_TYPES[counter % len(REQUEST_TYPES)]

        request_msg = Request(ID=ID, type=request_type)
        adapter.info(f"Requesting {request_type} agreement (ID: {ID})")
        await adapter.send(request_msg)

        await asyncio.sleep(2)  # Wait 2 seconds between requests


@adapter.reaction(Propose, Propose2)
async def handle_proposal(message):
    """React to a proposal by deciding whether to accept, reject, or do nothing."""
    ID = message["ID"]
    proposal = message["proposal"]

    adapter.info(f"Received proposal: {proposal} (ID: {ID})")

    # Wait a bit before responding to give time for decisions
    await asyncio.sleep(1)  # Short delay

    # Make a 3-way decision based on ID hash
    # 0: Accept, 1: Reject, 2: Do nothing (will be withdrawn)
    decision = sum(ord(c) for c in ID) % 3
    
    if decision == 0:
        # Accept the proposal
        signature = f"SIG-{ID}"
        accept_msg = Accept(
            ID=ID,
            proposal=proposal,
            signature=signature,
            decision="accepted",
            accepted="yes",
        )
        adapter.info(f"Accepting proposal (ID: {ID})")
        await adapter.send(accept_msg)
    elif decision == 1:
        # Reject the proposal
        reject_msg = Reject(
            ID=ID, proposal=proposal, decision="rejected", rejected="yes"
        )
        adapter.info(f"Rejecting proposal (ID: {ID})")
        await adapter.send(reject_msg)
    else:
        # Do nothing - this proposal will be withdrawn by the party after timeout
        adapter.info(f"No decision for proposal (ID: {ID}), waiting for withdrawal")


@adapter.reaction(Execute)
async def handle_execute(message):
    """React to an execution message."""
    ID = message["ID"]
    closed = message["closed"]

    adapter.info(f"Agreement executed (ID: {ID})")
    adapter.info(f"Status: {closed}")


@adapter.reaction(Ack)
async def handle_ack(message):
    """React to an acknowledgment message."""
    ID = message["ID"]
    closed = message["closed"]

    adapter.info(f"Rejection acknowledged (ID: {ID})")
    adapter.info(f"Status: {closed}")


@adapter.reaction(Withdraw)
async def handle_withdraw(message):
    """React to a withdrawal message."""
    ID = message["ID"]
    closed = message["closed"]

    adapter.info(f"Proposal withdrawn (ID: {ID})")
    adapter.info(f"Status: {closed}")


async def periodic_requests():
    """Periodically send new requests."""
    global counter

    while True:
        await asyncio.sleep(5)  # Wait 5 seconds between new requests

        counter += 1
        ID = f"counter-{counter}"
        request_type = REQUEST_TYPES[counter % len(REQUEST_TYPES)]

        request_msg = Request(ID=ID, type=request_type)
        adapter.info(f"Requesting {request_type} agreement (ID: {ID})")
        await adapter.send(request_msg)


if __name__ == "__main__":
    adapter.info("Starting CounterParty agent...")
    adapter.start(
        initiate_requests(),
        periodic_requests(),
    )
