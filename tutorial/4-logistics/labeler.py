"""
Implementation of the Labeler agent for the Logistics protocol.
"""

import asyncio
import logging
import uuid
import random
from bspl.adapter import Adapter
from configuration import agents, systems
from Logistics import Labeler, RequestLabel, Labeled

# Create the Labeler adapter
adapter = Adapter("labeler", systems, agents)

# Tracking for generated labels
generated_labels = {}


@adapter.enabled(Labeled)
async def generate_label(label_form):
    """
    Generate a shipping label when a label request is received.
    This is triggered when a RequestLabel message is received.
    """
    # TODO: Extract orderID and address from the form
    
    # TODO: Generate a tracking number
    
    # TODO: Return the form with the label parameter bound


if __name__ == "__main__":
    adapter.info("Starting Labeler agent...")
    adapter.start()