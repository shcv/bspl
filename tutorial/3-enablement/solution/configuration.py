"""
Configuration file for the Purchase protocol system.
This file defines the agents and their addresses, and sets up the protocol system.
"""

import bspl
from bspl.parsers.bspl import load_file

# Load the protocol specification from purchase.bspl
purchase_spec = load_file("purchase.bspl")
purchase = purchase_spec.export("Purchase")
from Purchase import Buyer, Seller

# Define agent addresses (localhost with different ports)
agents = {
    "buyer": [("localhost", 8001)],
    "seller": [("localhost", 8002)],
}

# Define the Purchase protocol system
systems = {
    "purchase": {
        "protocol": purchase,
        "roles": {Buyer: "buyer", Seller: "seller"},
    }
}
