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

# Define items to request quotes for
ITEMS_TO_REQUEST = ["ball", "bat", "glove", "helmet", "shoes"]
MAX_ACCEPTABLE_PRICE = 30.0  # Maximum price the buyer is willing to pay


async def send_rfqs():
    """Send RFQs for different items."""
    for item in ITEMS_TO_REQUEST:
        # Generate a unique ID for each request
        ID = str(uuid.uuid4())

        # Create and send RFQ message
        rfq = RFQ(ID=ID, item=item)
        await adapter.send(rfq)
        adapter.info(f"Sent RFQ for {item} with ID {ID}")

        # Small delay between requests
        await asyncio.sleep(0.5)


@adapter.reaction(Quote)
async def handle_quote(message):
    """React to a quote from the seller and decide whether to buy or reject."""
    adapter.info(f"Received quote for {message['item']} at price ${message['price']}")

    # Get the quoted price as a float
    price = float(message["price"])

    # Decide whether to buy or reject based on price
    if price <= MAX_ACCEPTABLE_PRICE:
        adapter.info(f"Accepting offer for {message['item']} at ${price}")
        buy_message = Buy(
            ID=message["ID"],
            item=message["item"],
            price=message["price"],
            done="accepted",
        )
        await adapter.send(buy_message)
    else:
        adapter.info(
            f"Rejecting offer for {message['item']} at ${price} (too expensive)"
        )
        reject_message = Reject(
            ID=message["ID"], price=message["price"], done="rejected"
        )
        await adapter.send(reject_message)


if __name__ == "__main__":
    adapter.info("Starting Buyer agent...")
    adapter.start(send_rfqs())
