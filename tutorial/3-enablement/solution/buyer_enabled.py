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
from Purchase import Buyer, RFQ, Quote, Buy, Reject

# Create the Buyer adapter
adapter = Adapter("buyer", systems, agents)

# Items to request quotes for
ITEMS = ["ball", "bat", "glove", "helmet", "shoes"]

# Maximum acceptable price
MAX_ACCEPTABLE_PRICE = 30.0


@adapter.decision(event=InitEvent)
async def initialize_requests(forms):
    """Start by sending RFQs for various items."""
    # Find all RFQ forms available
    rfq_forms = forms.messages(RFQ)

    attempts = []
    for rfq_form in rfq_forms:
        for item in ITEMS:
            ID = str(uuid.uuid4())
            adapter.info(f"Initiating RFQ for {item} with ID {ID}")
            attempts.append(rfq_form.bind(ID=ID, item=item))

    return attempts


@adapter.enabled(Buy)
async def make_purchase_decision(buy_form):
    """
    Decide whether to purchase an item based on price.
    This is only triggered when a Quote has been received, as Buy requires parameters from Quote to be enabled.
    """
    # Extract quote information
    item = buy_form["item"]
    price = float(buy_form["price"])

    adapter.info(f"Evaluating purchase of {item} at price ${price}")

    # Make decision based on price
    if price <= MAX_ACCEPTABLE_PRICE:
        adapter.info(f"Accepting offer for {item} at ${price}")
        return buy_form.bind(done="accepted")
    else:
        adapter.info(f"Price for {item} is too high, will reject")
        # We don't actually send the Buy message
        return None


@adapter.enabled(Reject)
async def make_reject_decision(reject_form):
    """
    Decide whether to reject a quote.
    Only triggered when a Quote has been received.
    """
    # Extract quote information
    ID = reject_form["ID"]
    price = float(reject_form["price"])

    # Reject if price is above our threshold
    if price > MAX_ACCEPTABLE_PRICE:
        adapter.info(f"Rejecting offer at price ${price} (too expensive)")
        return reject_form.bind(done="rejected")

    # Don't send reject message if price is acceptable
    return None


# React to quotes for logging purposes
@adapter.reaction(Quote)
async def log_quote(message):
    """Log reception of quotes."""
    adapter.info(f"Received quote for {message['item']} at price ${message['price']}")


if __name__ == "__main__":
    adapter.info("Starting Buyer agent (forms-based)...")
    adapter.start()
