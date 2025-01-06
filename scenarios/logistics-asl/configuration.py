"""
This scenario demonstrates implementing BSPL agents using AgentSpeak (ASL).
This is the ASL version of the logistics scenario, showing how to implement
the same behavior using a more declarative approach.
"""

import bspl

logistics = bspl.load_file("../logistics/logistics.bspl").export("Logistics")
from Logistics import Merchant, Wrapper, Labeler, Packer

agents = {
    "Merchant": [("127.0.0.1", 8000)],
    "Wrapper": [("127.0.0.1", 8001)],
    "Labeler": [("127.0.0.1", 8002)],
    "Packer": [("127.0.0.1", 8003)],
}

systems = {
    "logistics": {
        "protocol": logistics,
        "roles": {
            Merchant: "Merchant",
            Wrapper: "Wrapper",
            Labeler: "Labeler",
            Packer: "Packer",
        },
    },
} 