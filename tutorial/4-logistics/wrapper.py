"""
Implementation of the Wrapper agent for the Logistics protocol.
"""

import asyncio
import logging
import random
from bspl.adapter import Adapter
from configuration import agents, systems
from Logistics import Wrapper, RequestWrapping, Wrapped

# Create the Wrapper adapter
adapter = Adapter("wrapper", systems, agents)

# Wrapping materials based on item type
WRAPPING_MATERIALS = {
    "paperback": "bubble wrap",
    "cotton": "plastic bag",
    "ceramic": "foam padding",
    "plastic": "cardboard box",
    "gold": "velvet pouch",
    "default": "standard packaging",
}


@adapter.enabled(Wrapped)
async def wrap_item(wrap_form):
    """
    Wrap an item when a wrapping request is received.
    This is triggered when a RequestWrapping message is received.
    """
    # TODO: Extract orderID, itemID, and item type from the form
    
    # TODO: Select appropriate wrapping material based on item type
    
    # TODO: Return the form with the wrapping parameter bound


if __name__ == "__main__":
    adapter.info("Starting Wrapper agent...")
    adapter.start()