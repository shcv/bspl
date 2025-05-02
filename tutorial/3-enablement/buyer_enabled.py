"""
Implementation of the Buyer agent for the Purchase protocol using forms-based approach.
"""

import asyncio
import logging
import uuid
import random
from bspl.adapter import Adapter
from bspl.adapter.event import InitEvent
from configuration import agents, systems
from Purchase import RFQ, Quote, Buy, Reject

# Create the Buyer adapter
adapter = Adapter("buyer", systems, agents)

# Constants
ITEMS = ["ball", "bat", "glove", "helmet", "shoes"]
MAX_ACCEPTABLE_PRICE = 30.0  # Maximum price the buyer is willing to pay


@adapter.decision(event=InitEvent)
async def initialize_requests(forms):
    """
    Start by sending RFQs for various items.
    This is called when the adapter starts up.
    """
    # TODO: Find all RFQ forms available
    
    # TODO: For each item in ITEMS:
    # - Generate a unique ID
    # - Log RFQ initiation
    # - Bind ID and item to the form
    
    # TODO: Return the list of bound forms


@adapter.enabled(Buy)
async def make_purchase_decision(buy_form):
    """
    Decide whether to purchase an item based on price.
    This is only triggered when a Quote has been received,
    as Buy requires parameters from Quote to be enabled.
    """
    # TODO: Extract item and price information from form
    
    # TODO: Log evaluation of the purchase
    
    # TODO: If price is acceptable:
    # - Log acceptance
    # - Return the form bound with done="accepted"
    # TODO: If price is too high:
    # - Log rejection
    # - Return None (to not send Buy message)


@adapter.enabled(Reject)
async def make_reject_decision(reject_form):
    """
    Decide whether to reject a quote.
    Only triggered when a Quote has been received.
    """
    # TODO: Extract price information from form
    
    # TODO: If price is above threshold:
    # - Log rejection
    # - Return form bound with done="rejected"
    # TODO: If price is acceptable:
    # - Return None (to not send Reject message)


# Optional reaction for logging purposes
@adapter.reaction(Quote)
async def log_quote(message):
    """Log reception of quotes."""
    # TODO: Log received quote details


if __name__ == "__main__":
    adapter.info("Starting Buyer agent (forms-based)...")
    adapter.start()