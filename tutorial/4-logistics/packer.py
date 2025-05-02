"""
Implementation of the Packer agent for the Logistics protocol.
"""

import asyncio
import logging
from bspl.adapter import Adapter
from configuration import agents, systems
from Logistics import Packer, Wrapped, Labeled, Packed

# Create the Packer adapter
adapter = Adapter("packer", systems, agents)


@adapter.reaction(Wrapped)
async def handle_wrapped_item(message):
    """Process a wrapped item received from the Wrapper."""
    adapter.info(f"Received wrapped item for order {message['orderID']}, item {message['itemID']}")


@adapter.reaction(Labeled)
async def handle_shipping_label(message):
    """Process a shipping label received from the Labeler."""
    adapter.info(f"Received shipping label for order {message['orderID']}")


@adapter.enabled(Packed)
async def pack_item(packed_form):
    """
    Pack an item when both the wrapped item and shipping label are available.
    This is triggered when both a Wrapped and Labeled message have been received
    for the same orderID.
    """
    # TODO: Extract orderID and itemID from the form
    
    # TODO: Return the form with the status parameter bound as "packed"


if __name__ == "__main__":
    adapter.info("Starting Packer agent...")
    adapter.start()