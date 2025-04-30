"""
Implementation of the Packer agent for the Logistics protocol.
This agent combines wrapped items with shipping labels.
"""

import logging
from bspl.adapter import Adapter
from configuration import agents, systems
from Logistics import Packer, Wrapped, Labeled, Packed

# Create the Packer adapter
adapter = Adapter("packer", systems, agents)


@adapter.enabled(Packed)
async def pack_item(packed_form):
    """
    Pack an item when both wrapping and label are available.
    This is called automatically when both Wrapped and Labeled messages
    have been received for a specific orderID.
    """
    # Extract information from the form
    orderID = packed_form["orderID"]
    itemID = packed_form["itemID"]
    wrapping = packed_form["wrapping"]
    label = packed_form["label"]

    # Log the packing operation
    adapter.info(f"Packing item {itemID} from order {orderID}")
    adapter.info(f"Item is wrapped with {wrapping}")
    adapter.info(f"Using shipping label: {label}")

    # Determine the packing status
    # In a real application, this might include quality checks or other business logic
    status = "PACKED"

    # Bind the status to the form
    return packed_form.bind(status=status)


# React to wrapped items and labels for logging purposes
@adapter.reaction(Wrapped)
async def log_wrapped_item(message):
    """Log when a wrapped item is received."""
    adapter.info(
        f"Received wrapped item {message['item']} (ID: {message['itemID']}) from order {message['orderID']}"
    )
    adapter.info(f"Item is wrapped with {message['wrapping']}")


@adapter.reaction(Labeled)
async def log_label(message):
    """Log when a label is received."""
    adapter.info(
        f"Received shipping label {message['label']} for order {message['orderID']}"
    )


if __name__ == "__main__":
    adapter.info("Starting Packer agent...")
    adapter.start()
