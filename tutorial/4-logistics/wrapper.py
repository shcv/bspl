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

# Define wrapping materials for different item types
WRAPPING_MATERIALS = {
    "fragile": "bubblewrap",
    "standard": "paper",
    "clothing": "plastic",
    "book": "cardboard",
}


def select_wrapping_material(item):
    """Select appropriate wrapping material based on item type."""
    return WRAPPING_MATERIALS.get(item.lower(), WRAPPING_MATERIALS["standard"])


@adapter.enabled(Wrapped)
async def wrap_item(wrap_form):
    """
    Wrap an item when a wrapping request is received.
    This is triggered when a RequestWrapping message is received.
    """
    # TODO: Extract orderID, itemID, and item type from the form

    # TODO: Select the appropriate wrapping material
    # wrapping = select_wrapping_material(item)

    # TODO: Return the form with the wrapping parameter bound


if __name__ == "__main__":
    adapter.info("Starting Wrapper agent...")
    adapter.start()
