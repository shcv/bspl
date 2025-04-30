"""
Implementation of the Buyer agent for the Purchase protocol.
"""

import asyncio
import logging
import uuid
from bspl.adapter import Adapter
from configuration import agents, systems
from Purchase import Buyer, RFQ, Quote, Buy, Reject

# Create the Buyer adapter
adapter = Adapter("buyer", systems, agents)


# TODO: Implement a function to send RFQs for different items
async def send_rfqs():
    """Send RFQs for different items."""
    # TODO: Define items to request quotes for
    items = []  # Add your items here

    for item in items:
        # TODO: Generate a unique ID
        ID = ""

        # TODO: Create and send RFQ message with async adapter.send()

        # Small delay between requests
        await asyncio.sleep(0.5)


# TODO: Implement a reaction handler for Quote messages
@adapter.reaction(Quote)
async def handle_quote(message):
    """React to a quote from the seller and decide whether to buy or reject."""
    # TODO: Extract information from quote message

    # TODO: Decide whether to buy or reject based on price
    # If price is acceptable:
    #    Send Buy message
    # Else:
    #    Send Reject message


if __name__ == "__main__":
    adapter.info("Starting Buyer agent...")  # use adapter logging
    # TODO: Start the adapter with the RFQ initiation function
