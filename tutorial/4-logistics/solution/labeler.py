"""
Implementation of the Labeler agent for the Logistics protocol.
This agent generates shipping labels based on addresses.
"""

import logging
import uuid
import random
from bspl.adapter import Adapter
from configuration import agents, systems
from Logistics import Labeler, RequestLabel, Labeled

# Create the Labeler adapter
adapter = Adapter("labeler", systems, agents)


@adapter.enabled(Labeled)
async def generate_label(labeled_form):
    """
    Generate a shipping label when a request is received.
    This is called when the RequestLabel message has been received.
    """
    # Extract information from the request
    orderID = labeled_form["orderID"]
    address = labeled_form["address"]

    # Generate a unique tracking number
    tracking_number = f"TRACK-{str(uuid.uuid4())[:8]}"
    
    # Create a formatted label
    label = tracking_number

    adapter.info(f"Generated shipping label {label} for order {orderID}")
    adapter.info(f"Shipping to: {address}")

    # Bind the label to the form
    return labeled_form.bind(label=label)


# React to label requests for logging purposes
@adapter.reaction(RequestLabel)
async def log_label_request(message):
    """Log when a label request is received."""
    adapter.info(
        f"Received label request for order {message['orderID']} to address: {message['address']}"
    )


if __name__ == "__main__":
    adapter.info("Starting Labeler agent...")
    adapter.start()
