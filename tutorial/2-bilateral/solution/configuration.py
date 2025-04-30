"""
Configuration file for the ExecuteBilateralAgreement protocol system.
This file defines the agents and their addresses, and sets up the protocol system.
"""

import bspl
from bspl.parsers.bspl import load_file

# Load the protocol specification
bilateral_spec = load_file("bilateral.bspl")
bilateral = bilateral_spec.export("BilateralAgreement")
from BilateralAgreement import Party, CounterParty

# Define agent addresses
agents = {
    "party": [("localhost", 8001)],
    "counterparty": [("localhost", 8002)],
}

# Define the protocol system
systems = {
    "agreement": {
        "protocol": bilateral,
        "roles": {Party: "party", CounterParty: "counterparty"},
    }
}
