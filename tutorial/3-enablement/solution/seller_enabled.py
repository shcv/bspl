"""
Implementation of the Seller agent for the Purchase protocol using forms-based approach.
"""

import asyncio
import logging
import random
from bspl.adapter import Adapter
from configuration import agents, systems
from Purchase import Seller, RFQ, Quote, Buy, Reject

# Create the Seller adapter
adapter = Adapter("seller", systems, agents)

# Define a pricing model for items
ITEM_PRICES = {"ball": 15.0, "bat": 35.0, "glove": 25.0, "helmet": 45.0, "shoes": 60.0}


def get_price(item):
    """Get the base price for an item and add small random variation."""
    base_price = ITEM_PRICES.get(item, 20.0)  # Default price if item not in dictionary
    variation = random.uniform(-2.0, 5.0)  # Add some variation
    return round(base_price + variation, 2)


@adapter.enabled(Quote)
async def generate_quote(quote_form):
    """
    Generate a quote when an RFQ is received.
    This is triggered automatically when an RFQ is received that enables a Quote.
    """
    # Extract RFQ information
    item = quote_form["item"]
    ID = quote_form["ID"]

    adapter.info(f"Generating quote for {item} (ID: {ID})")

    # Calculate price for the item
    price = get_price(item)

    # Bind price to the Quote form
    adapter.info(f"Offering {item} at price ${price}")
    return quote_form.bind(price=str(price))


@adapter.reaction(Reject)
async def handle_reject(message):
    """React to a Reject message."""
    adapter.info(f"Buyer rejected offer at price ${message['price']}")


if __name__ == "__main__":
    adapter.info("Starting Seller agent (forms-based)...")
    adapter.start()
