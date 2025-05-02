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
adapter = Adapter("merchant", systems, agents)

# Constants
SHIPPING_ADDRESSES = [
    "123 Main St., New York, NY 10001",
    "456 Oak Ave., Los Angeles, CA 90001",
    "789 Pine Rd., Chicago, IL 60007",
    "321 Maple Dr., Houston, TX 77001",
]

ITEMS = {
    "book": "paperback",
    "shirt": "cotton",
    "mug": "ceramic",
    "toy": "plastic",
    "jewelry": "gold",
}

# Track orders and items
orders = {}  # To track orders and their items


@adapter.decision(event=InitEvent)
async def create_orders(forms):
    """Start by creating orders and requesting labels and item wrapping."""
    # TODO: Create several orders with unique orderIDs
    # TODO: For each order:
    #   - Generate a shipping address
    #   - Request a shipping label
    #   - Add multiple items to the order
    #   - Request wrapping for each item


@adapter.reaction(Packed)
async def handle_packed(message):
    """
    React to a Packed message from the Packer.
    Update order status and check if order is complete.
    """
    # TODO: Process packed item notification


async def order_status_monitor():
    """Periodically check and log the status of all orders."""
    while True:
        for orderID, order in orders.items():
            total_items = len(order["items"])
            packed_items = sum(1 for item in order["items"].values() if item["status"] == "packed")
            adapter.info(f"Order {orderID} status: {packed_items}/{total_items} items packed")
            
            # Check if order is complete
            if packed_items == total_items and total_items > 0:
                adapter.info(f"Order {orderID} is now complete!")
        
        await asyncio.sleep(5)  # Check every 5 seconds


if __name__ == "__main__":
    adapter.info("Starting Merchant agent...")
    # Start the adapter with background tasks
    asyncio.create_task(order_status_monitor())
    adapter.start()