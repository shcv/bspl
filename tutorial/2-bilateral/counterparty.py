"""
Implementation of the CounterParty agent for the BilateralAgreement protocol.
"""

import asyncio
import logging
import uuid
import random
from bspl.adapter import Adapter
from configuration import agents, systems
# Import relevant messages from the protocol
from BilateralAgreement import Request, Propose, Propose2, Accept, Reject, Execute, Ack, Withdraw

# Create the CounterParty adapter
adapter = Adapter("counterparty", systems, agents)

# Constants and settings
REQUEST_TYPES = ["standard", "premium", "basic"]
ACCEPT_PROBABILITY = 0.6  # 60% chance to accept proposals


async def send_requests():
    """Periodically send requests for different agreement types."""
    # TODO: Implement logic to periodically send requests
    # - Generate unique IDs
    # - Select random agreement types
    # - Create and send Request messages
    # - Add appropriate delay between requests


@adapter.reaction(Propose)
@adapter.reaction(Propose2)
async def handle_proposal(message):
    """
    React to a proposal by deciding whether to accept or reject.
    
    Args:
        message: The Propose or Propose2 message from Party
    """
    # TODO: Extract information from proposal message
    
    # TODO: Decide whether to accept or reject (using random probability)
    
    # TODO: If accepting:
    #   - Generate a digital signature
    #   - Send Accept message with signature
    # TODO: If rejecting:
    #   - Send Reject message


@adapter.reaction(Execute)
async def handle_execution(message):
    """
    React to an Execute message - agreement has been executed.
    
    Args:
        message: The Execute message confirming agreement execution
    """
    # TODO: Process executed agreement
    # - Log details of executed agreement
    # - Implement any follow-up actions


@adapter.reaction(Ack)
async def handle_acknowledgment(message):
    """
    React to an Ack message - Party has acknowledged our rejection.
    
    Args:
        message: The Ack message
    """
    # TODO: Process rejection acknowledgment
    # - Log details of rejected agreement


@adapter.reaction(Withdraw)
async def handle_withdrawal(message):
    """
    React to a Withdraw message - Party has withdrawn their proposal.
    
    Args:
        message: The Withdraw message
    """
    # TODO: Process withdrawal
    # - Log details of withdrawn proposal


if __name__ == "__main__":
    adapter.info("Starting CounterParty agent...")
    # TODO: Start the adapter with the send_requests function