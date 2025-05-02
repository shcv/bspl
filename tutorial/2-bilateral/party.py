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
    """Periodically initiate direct proposals without prior requests."""
    # TODO: Implement logic to periodically send direct proposals (Propose2)
    # - Generate unique IDs
    # - Select random proposal types
    # - Create and send Propose2 messages
    # - Add appropriate delay between proposals


@adapter.reaction(Accept)
async def handle_accept(message):
    """
    React to an Accept message - CounterParty has accepted the proposal.
    
    Args:
        message: The Accept message containing signature and decision
    """
    # TODO: Process acceptance and execute the agreement
    # - Extract signature and other details
    # - Send Execute message to confirm agreement execution


@adapter.reaction(Reject)
async def handle_reject(message):
    """
    React to a Reject message - CounterParty has rejected the proposal.
    
    Args:
        message: The Reject message
    """
    # TODO: Handle rejection by acknowledging it
    # - Send Ack message to acknowledge rejection


async def withdraw_inactive_proposals():
    """Periodically check for and withdraw proposals that have been pending too long."""
    # TODO: Implement logic to withdraw pending proposals after a timeout
    # - Track proposals with timestamps
    # - Check for proposals beyond timeout threshold
    # - Send Withdraw message for timed-out proposals


if __name__ == "__main__":
    adapter.info("Starting Party agent...")
    # TODO: Start the adapter with the initiate_proposals function
    # TODO: Start the withdraw_inactive_proposals background task