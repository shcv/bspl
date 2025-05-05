"""
Implementation of the Buyer agent for the Purchase protocol.
"""

import asyncio
import logging
import uuid
from bspl.adapter import Adapter
from configuration import agents, systems
from Purchase import RFQ, Quote, Buy, Reject

# Create the Buyer adapter
adapter = Adapter("buyer", systems, agents)

# Items to request quotes for
ITEMS = ["ball", "bat", "glove", "helmet", "shoes"]

# Maximum acceptable price
MAX_ACCEPTABLE_PRICE = 30.0


# TODO: Implement a function to send RFQs for different items
async def send_rfqs():
    """Send RFQs for different items."""
    # TODO: Define items to request quotes for
    items = ITEMS

    for item in items:
        # TODO: Generate a unique ID
        ID = ""

        # TODO: Create and send RFQ message with async adapter.send()

        # Small delay between requests (optional)
        # await asyncio.sleep(0.1)


# TODO: Implement a reaction handler for Quote messages
@adapter.reaction(Quote)
async def handle_quote(message):
    """React to a quote from the seller and decide whether to buy or reject."""
    # TODO: Extract information from quote message

    # TODO: Decide whether to buy or reject based on price
    # If price is acceptable (price <= MAX_ACCEPTABLE_PRICE):
    #    Send Buy message
    # Else:
    #    Send Reject message


if __name__ == "__main__":
    adapter.info("Starting Buyer agent...")  # use adapter logging
    # TODO: Start the adapter with the RFQ initiation function
