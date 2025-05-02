"""
Implementation of the Party agent for the BilateralAgreement protocol.
"""

import asyncio
import logging
from bspl.adapter import Adapter
from configuration import agents, systems
from BilateralAgreement import (
    Party,
    Request,
    Propose,
    Propose2,
    Accept,
    Reject,
    Execute,
    Ack,
    Withdraw,
)

# Create the Party adapter
adapter = Adapter("party", systems, agents)

# Track active proposals
active_proposals = {}

# Simple counter for IDs
counter = 0

# Simple proposal templates
PROPOSALS = [
    "Buy 10 widgets for $500",
    "Provide consulting for 20 hours",
    "Enter 50/50 partnership agreement",
    "License technology for 1 year",
]


async def send_proposal(ID, proposal_type, proposal, direct=True):
    """Send a proposal and automatically withdraw it after 3 seconds if no response.
    
    Args:
        ID: The unique identifier for the proposal
        proposal_type: The type of proposal
        proposal: The proposal content
        direct: If True, sends a Propose2 message (direct proposal)
               If False, sends a Propose message (response to request)
    """
    # Send the appropriate proposal message
    if direct:
        propose_msg = Propose2(ID=ID, type=proposal_type, proposal=proposal)
        adapter.info(f"Initiating proposal: {proposal} (ID: {ID})")
    else:
        propose_msg = Propose(ID=ID, type=proposal_type, proposal=proposal)
        adapter.info(f"Sending proposal: {proposal}")
    
    await adapter.send(propose_msg)
    
    # Track the proposal
    active_proposals[ID] = proposal
    
    # Schedule withdrawal after 3 seconds if no response received
    asyncio.create_task(schedule_withdrawal(ID, proposal))


async def schedule_withdrawal(ID, proposal):
    """Schedule a withdrawal after 3 seconds if the proposal is still active."""
    await asyncio.sleep(3)  # Wait 3 seconds
    
    # Check if proposal is still active (hasn't been accepted or rejected)
    if ID in active_proposals:
        adapter.info(f"No response received for proposal {ID}, withdrawing...")
        withdraw_msg = Withdraw(
            ID=ID, proposal=proposal, decision="withdrawn", closed="withdrawn"
        )
        await adapter.send(withdraw_msg)
        
        # Remove from active proposals
        del active_proposals[ID]


async def initiate_proposals():
    """Initiate proposals directly."""
    global counter

    for i in range(2):  # Start with 2 proposals
        counter += 1
        ID = f"party-{counter}"
        proposal_type = f"type-{counter % 4}"
        proposal = PROPOSALS[counter % len(PROPOSALS)]

        await send_proposal(ID, proposal_type, proposal, direct=True)
        await asyncio.sleep(2)  # Wait 2 seconds between proposals


@adapter.reaction(Request)
async def handle_request(message):
    """React to a request by generating a proposal."""
    ID = message["ID"]
    request_type = message["type"]

    adapter.info(f"Received request: {request_type} (ID: {ID})")

    # Choose proposal based on request ID number
    id_num = int(ID.split("-")[1]) % len(PROPOSALS)
    proposal = PROPOSALS[id_num]

    await send_proposal(ID, request_type, proposal, direct=False)


@adapter.reaction(Accept)
async def handle_accept(message):
    """React to an acceptance by executing the agreement."""
    ID = message["ID"]
    signature = message["signature"]

    adapter.info(f"Proposal accepted for ID: {ID}")
    adapter.info(f"Signature: {signature}")

    execute_msg = Execute(ID=ID, signature=signature, closed="executed")
    adapter.info(f"Executing agreement: {ID}")
    await adapter.send(execute_msg)

    if ID in active_proposals:
        del active_proposals[ID]


@adapter.reaction(Reject)
async def handle_reject(message):
    """React to a rejection by acknowledging it."""
    ID = message["ID"]

    adapter.info(f"Proposal rejected for ID: {ID}")

    ack_msg = Ack(
        ID=ID,
        proposal=message["proposal"],
        rejected=message["rejected"],
        closed="rejected",
    )
    adapter.info(f"Acknowledging rejection: {ID}")
    await adapter.send(ack_msg)

    if ID in active_proposals:
        del active_proposals[ID]


if __name__ == "__main__":
    adapter.info("Starting Party agent...")
    adapter.start(
        initiate_proposals(),
    )
