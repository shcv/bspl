"""
Implementation of the Merchant agent for the Logistics protocol.
This agent initiates orders and handles packed confirmations.
"""

import asyncio
import logging
import uuid
import random
from bspl.adapter import Adapter
from bspl.adapter.event import InitEvent
from configuration import agents, systems
from Logistics import Merchant, RequestLabel, RequestWrapping, Packed

# Create the Merchant adapter
adapter = Adapter("merchant", systems, agents, in_place=True)

# Sample items that can be ordered
ITEMS = ["ball", "plate", "glass", "book", "toy", "electronics", "clothing", "jewelry"]

# Sample addresses for shipping
ADDRESSES = [
    "123 Main St, Anytown, AN 12345",
    "456 Oak Ave, Springfield, SP 67890",
    "789 Pine Rd, Liberty, LB 13579",
    "321 Cedar Ln, Westville, WV 24680",
    "654 Maple Dr, Eastwood, EW 97531",
]

# Track orders and their items
orders = {}  # orderID -> {itemID -> item}
packed_items = {}  # orderID -> {itemID -> status}


@adapter.decision(event=InitEvent)
async def create_orders(forms):
    """Create several orders with multiple items each."""
    # Generate 3 different orders
    for _ in range(3):
        # Generate a unique order ID
        orderID = str(uuid.uuid4())

        # Select a random shipping address
        address = random.choice(ADDRESSES)

        # Initialize order tracking
        orders[orderID] = {}
        packed_items[orderID] = {}

        # Request label for the order
        for request_label_form in forms.messages(RequestLabel):
            adapter.info(f"Creating order {orderID} with shipping to {address}")
            request_label_form.bind(orderID=orderID, address=address)
            break  # Only need one label per order


@adapter.enabled(RequestWrapping)
async def request_wrapping(request_wrapping_form):
    # Number of items in this order (2-4 items)
    num_items = random.randint(2, 4)

    for i in range(num_items):
        orderID = request_wrapping_form["orderID"]
        # Generate a unique item ID
        itemID = str(i + 1)  # Simple sequential IDs for clarity

        # Select a random item
        item = random.choice(ITEMS)

        # Track the item
        orders[orderID][itemID] = item

        # Request wrapping
        adapter.info(f"Adding item {item} (ID: {itemID}) to order {orderID}")
        request_wrapping_form.bind(itemID=itemID, item=item)


@adapter.reaction(Packed)
async def handle_packed(message):
    """Handle packed confirmation from the Packer."""
    orderID = message["orderID"]
    itemID = message["itemID"]
    status = message["status"]

    # Update packed status
    if orderID in packed_items:
        packed_items[orderID][itemID] = status

        # Get the item that was packed
        item = orders.get(orderID, {}).get(itemID, "unknown item")

        adapter.info(
            f"Item {item} (ID: {itemID}) from order {orderID} has been packed with status: {status}"
        )

        # Check if the entire order is packed
        if len(packed_items[orderID]) == len(orders[orderID]):
            adapter.info(
                f"Order {orderID} is now complete with {len(orders[orderID])} items packed!"
            )

            # In a real application, you might trigger additional business logic here
            # Such as sending a notification to the customer or initiating delivery


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
    adapter.start(monitor_orders())  # Start background monitoring task
