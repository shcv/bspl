"""
Configuration file for the Logistics protocol system.
This file defines the agents and their addresses, and sets up the protocol system.
"""

import bspl
from bspl.parsers.bspl import load_file

# Load the protocol specification
logistics_spec = load_file("logistics.bspl")
logistics = logistics_spec.export("Logistics")
from Logistics import Merchant, Wrapper, Labeler, Packer

# Define agent addresses
agents = {
    "merchant": [("localhost", 8001)],
    "wrapper": [("localhost", 8002)],
    "labeler": [("localhost", 8003)],
    "packer": [("localhost", 8004)],
}

# Define the Logistics protocol system
systems = {
    "logistics": {
        "protocol": logistics,
        "roles": {
            Merchant: "merchant",
            Wrapper: "wrapper",
            Labeler: "labeler",
            Packer: "packer",
        },
    }
}
