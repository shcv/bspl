"""
Configuration file for the Purchase protocol system.
This file defines the agents and their addresses, and sets up the protocol system.
"""

import bspl

# Load the protocol specification from purchase.bspl
purchase = bspl.load_file("purchase.bspl").export("Purchase")
from Purchase import B, S

# Define agent addresses (localhost with different ports)
agents = {
    "buyer": [("localhost", 8001)],
    "seller": [("localhost", 8002)],
}

# Define the Purchase protocol system
systems = {
    "purchase": {
        "protocol": purchase,
        "roles": {B: "buyer", S: "seller"},
    }
}
