"""
Implementation of the Wrapper agent for the Logistics protocol.
This agent handles wrapping items with appropriate materials.
"""

import logging
from bspl.adapter import Adapter
from configuration import agents, systems
from Logistics import Wrapper, RequestWrapping, Wrapped

# Create the Wrapper adapter
adapter = Adapter("wrapper", systems, agents)

# Define fragile items that need bubble wrap
FRAGILE_ITEMS = ["glass", "plate", "electronics", "jewelry"]

# Define wrapping materials for different item types
WRAPPING_MATERIALS = {
    "fragile": "bubblewrap",
    "standard": "paper",
    "clothing": "plastic",
    "book": "cardboard",
}


def select_wrapping_material(item):
    """Select appropriate wrapping material based on item type."""
    if item.lower() in FRAGILE_ITEMS:
        return WRAPPING_MATERIALS["fragile"]
    elif item.lower() == "clothing":
        return WRAPPING_MATERIALS["clothing"]
    elif item.lower() == "book":
        return WRAPPING_MATERIALS["book"]
    else:
        return WRAPPING_MATERIALS["standard"]


@adapter.enabled(Wrapped)
async def wrap_item(wrapped_form):
    """
    Wrap an item when a wrapping request is received.
    This is called when the RequestWrapping message has been received.
    """
    # Extract information from the request
    orderID = wrapped_form["orderID"]
    itemID = wrapped_form["itemID"]
    item = wrapped_form["item"]

    # Select the appropriate wrapping material
    wrapping = select_wrapping_material(item)

    adapter.info(f"Wrapping {item} (ID: {itemID}) from order {orderID} with {wrapping}")

    # Bind the wrapping material to the form
    return wrapped_form.bind(wrapping=wrapping)


# React to wrapping requests for logging purposes
@adapter.reaction(RequestWrapping)
async def log_wrapping_request(message):
    """Log when a wrapping request is received."""
    adapter.info(
        f"Received wrapping request for item {message['item']} (ID: {message['itemID']}) in order {message['orderID']}"
    )


if __name__ == "__main__":
    adapter.info("Starting Wrapper agent...")
    adapter.start()
