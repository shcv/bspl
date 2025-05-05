"""
Implementation of the Party agent for the BilateralAgreement protocol.
"""

import asyncio
import logging
import uuid
import random
from bspl.adapter import Adapter
from configuration import agents, systems
# Import relevant messages from the protocol
from BilateralAgreement import Request, Propose, Propose2, Accept, Reject, Execute, Ack, Withdraw

# Create the Party adapter
adapter = Adapter("party", systems, agents)

# Constants and settings
PROPOSAL_TYPES = ["standard", "premium", "basic"]
PROPOSAL_TERMS = {
    "standard": "Standard terms with 30-day completion",
    "premium": "Premium terms with priority service",
    "basic": "Basic terms with lower cost",
}

# Sample proposal templates
PROPOSALS = [
    "Buy 10 widgets for $500",
    "Provide consulting for 20 hours"
]

# Simple counter for IDs
counter = 0


@adapter.reaction(Request)
async def handle_request(message):
    """
    React to a Request by generating a proposal.
    
    Args:
        message: The Request message from CounterParty
    """
    # TODO: Extract information from Request message
    
    # TODO: Generate appropriate proposal terms based on request type
    
    # TODO: Send Propose message to CounterParty


async def initiate_proposals():
    """Initiate direct proposals without prior requests."""
    global counter
    
    # TODO: Implement logic to send direct proposals (Propose2)
    # - Increment counter and generate ID using counter (e.g., "party-1")
    # - Select proposal type and content
    # - Create and send Propose2 message
    # - Schedule withdrawal for the proposal


@adapter.reaction(Accept)
async def handle_accept(message):
    """
    React to an Accept message - CounterParty has accepted the proposal.
    
    Args:
        message: The Accept message containing signature and decision
    """
    # TODO: Process acceptance and execute the agreement
    # - Extract ID and signature from the message
    # - Create and send Execute message to confirm agreement execution
    # - The Execute message completes the agreement process


@adapter.reaction(Reject)
async def handle_reject(message):
    """
    React to a Reject message - CounterParty has rejected the proposal.
    
    Args:
        message: The Reject message
    """
    # TODO: Handle rejection by acknowledging it
    # - Extract ID, proposal, and rejected status from the message
    # - Create and send Ack message to acknowledge rejection
    # - The Ack message closes the agreement process


async def schedule_withdrawal(ID, proposal):
    """Schedule a withdrawal after a timeout if no response is received."""
    # TODO: Implement logic to withdraw a specific proposal after a timeout
    # - Wait for a short period (e.g., 0.3 seconds)
    # - Create Withdraw message with ID and proposal parameters
    # - Set the decision and closed status
    # - Send Withdraw message
    # - The protocol will automatically block the withdrawal if already accepted/rejected


if __name__ == "__main__":
    adapter.info("Starting Party agent...")
    # TODO: Start the adapter with the initiate_proposals function
    # TODO: Start the withdraw_inactive_proposals background task