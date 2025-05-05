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

# Define agent addresses (0.0.0.0 with different ports)
agents = {
    "merchant": [("0.0.0.0", 8001)],
    "wrapper": [("0.0.0.0", 8002)],
    "labeler": [("0.0.0.0", 8003)],
    "packer": [("0.0.0.0", 8004)],
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
