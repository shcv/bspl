"""
Implementation of the Seller agent for the Purchase protocol.
"""

import asyncio
import logging
import random
from bspl.adapter import Adapter
from configuration import agents, systems

# Import the Purchase protocol roles and messages
from Purchase import RFQ, Quote, Buy, Reject


# Create the Seller adapter
adapter = Adapter("seller", systems, agents)

# Simple pricing model
ITEM_PRICES = {"ball": 15.0, "bat": 35.0, "glove": 25.0, "helmet": 45.0, "shoes": 60.0}

def get_price(item):
    """Get the base price for an item and add small random variation."""
    base_price = ITEM_PRICES.get(item, 20.0)  # Default price if item not in dictionary
    variation = random.uniform(-2.0, 5.0)  # Add some variation
    return round(base_price + variation, 2)


@adapter.reaction(RFQ)
async def handle_rfq(message):
    """
    React to an RFQ by sending a quote with a price.

    Args:
        message: The RFQ message containing item and ID
    """
    # TODO: Extract information from RFQ message using message["parameter"]

    # TODO: Calculate price for the item using get_price()

    # TODO: Create and send Quote message with async adapter.send(...)
    adapter.info("Received RFQ for item")  # adapter provides logging


@adapter.reaction(Buy)
async def handle_buy(message):
    """
    React to a Buy message - buyer has accepted the quote.

    Args:
        message: The Buy message containing item, price and ID
    """
    # TODO: Process the accepted offer
    adapter.info("Buyer accepted offer")


@adapter.reaction(Reject)
async def handle_reject(message):
    """
    React to a Reject message - buyer has rejected the quote.

    Args:
        message: The Reject message containing price and ID
    """
    # TODO: Handle rejection (e.g., log it, update statistics)
    adapter.info("Buyer rejected offer")


if __name__ == "__main__":
    adapter.info("Starting Seller agent...")
    adapter.start()
