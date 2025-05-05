"""
Implementation of the Merchant agent for the Logistics protocol.
"""

import asyncio
import logging
import uuid
import random
from bspl.adapter import Adapter
from bspl.adapter.event import InitEvent
from configuration import agents, systems
from Logistics import RequestLabel, RequestWrapping, Packed

# Create the Merchant adapter
# in_place=True allows us to bind parameters on the message forms to make and send instances,
# without needing to collect and return them
adapter = Adapter("merchant", systems, agents, in_place=True)

# Constants
ADDRESSES = [
    "123 Main St, Anytown, AN 12345",
    "456 Oak Ave, Springfield, SP 67890",
    "789 Pine Rd, Liberty, LB 13579",
    "321 Cedar Ln, Westville, WV 24680",
    "654 Maple Dr, Eastwood, EW 97531",
]

# Sample items that can be ordered
ITEMS = ["ball", "plate", "glass", "book", "toy", "electronics", "clothing", "jewelry"]

# Track orders and their items
orders = {}  # orderID -> {itemID -> item}
packed_items = {}  # orderID -> {itemID -> status}


@adapter.decision(event=InitEvent)
async def create_orders(forms):
    """Start by creating orders and requesting labels and item wrapping."""
    # TODO: Create several orders with unique orderIDs
    # TODO: For each order:
    #   - Generate a shipping address
    #   - Request a shipping label
    #   - Initialize order tracking data structures


@adapter.enabled(RequestWrapping)
async def request_wrapping(request_wrapping_form):
    """Add items to an order and request wrapping for them."""
    # TODO: For each order:
    #   - Generate unique item IDs
    #   - Select random items
    #   - Track the items in the orders dictionary
    #   - Bind parameters to the request_wrapping_form


@adapter.reaction(Packed)
async def handle_packed(message):
    """
    React to a Packed message from the Packer.
    Update order status and check if order is complete.
    """
    # TODO: Process packed item notification
    # - Extract orderID, itemID, and status from message
    # - Update packed_items dictionary with the item's status
    # - Check if all items in this order are now packed
    # - Log order completion if all items are packed


async def monitor_orders():
    """Periodically check order status and log summary."""
    while True:
        await asyncio.sleep(2)  # Check every 2 seconds

        if not orders:
            continue

        adapter.info("--- Order Status Summary ---")
        for orderID, items in orders.items():
            packed_count = len(packed_items.get(orderID, {}))
            total_items = len(items)
            adapter.info(f"Order {orderID}: {packed_count}/{total_items} items packed")
        adapter.info("---------------------------")


if __name__ == "__main__":
    adapter.info("Starting Merchant agent...")
    # Start the adapter with background tasks
    asyncio.create_task(monitor_orders())
    adapter.start()