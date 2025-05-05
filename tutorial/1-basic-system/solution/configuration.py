"""
Configuration file for the Purchase protocol system.
This file defines the agents and their addresses, and sets up the protocol system.
"""

import bspl

# Load the protocol specification from purchase.bspl
purchase = bspl.load_file("purchase.bspl").export("Purchase")
from Purchase import Buyer, Seller

# Define agent addresses (0.0.0.0 with different ports)
agents = {
    "buyer": [("0.0.0.0", 8001)],
    "seller": [("0.0.0.0", 8002)],
}

# Define the Purchase protocol system
systems = {
    "purchase": {
        "protocol": purchase,
        "roles": {Buyer: "buyer", Seller: "seller"},
    }
}
