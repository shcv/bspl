"""
Implementation of the Seller agent for the Purchase protocol.
"""

import asyncio
import logging
import random
from bspl.adapter import Adapter
from configuration import agents, systems
from Purchase import Seller, RFQ, Quote, Buy, Reject

# Create the Seller adapter
adapter = Adapter("seller", systems, agents)


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
