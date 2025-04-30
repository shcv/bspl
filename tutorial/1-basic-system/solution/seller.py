"""
Implementation of the Seller agent for the Purchase protocol.
"""

import asyncio
import logging
import random
from bspl.adapter import Adapter
from configuration import agents, systems
from Purchase import RFQ, Quote, Buy, Reject

# Create the Seller adapter
adapter = Adapter("seller", systems, agents)

# Define a pricing function for items
ITEM_PRICES = {"ball": 15.0, "bat": 35.0, "glove": 25.0, "helmet": 45.0, "shoes": 60.0}


def get_price(item):
    """Get the base price for an item and add small random variation."""
    base_price = ITEM_PRICES.get(item, 20.0)  # Default price if item not in dictionary
    variation = random.uniform(-2.0, 5.0)  # Add some variation
    return round(base_price + variation, 2)


@adapter.reaction(RFQ)
async def handle_rfq(message):
    """React to an RFQ by sending a quote with a price."""
    item = message["item"]
    ID = message["ID"]

    adapter.info(f"Received RFQ for {item} with ID {ID}")

    # Calculate price for the item
    price = get_price(item)

    # Create and send Quote message
    quote = Quote(ID=ID, item=item, price=str(price))

    adapter.info(f"Sending quote for {item} at price ${price}")
    await adapter.send(quote)


@adapter.reaction(Buy)
async def handle_buy(message):
    """React to a Buy message."""
    adapter.info(
        f"Buyer accepted offer for {message['item']} at price ${message['price']}"
    )
    adapter.info(f"Processing order for {message['item']}...")
    # In a real implementation, this would trigger order processing


@adapter.reaction(Reject)
async def handle_reject(message):
    """React to a Reject message."""
    adapter.info(f"Buyer rejected offer at price ${message['price']}")
    # Could implement some business logic here, like recording statistics or
    # preparing a better offer next time


if __name__ == "__main__":
    adapter.info("Starting Seller agent...")
    adapter.start()
