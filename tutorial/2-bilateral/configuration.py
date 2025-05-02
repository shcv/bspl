"""
Configuration file for the BilateralAgreement protocol system.
"""

import bspl

# Load the protocol and export it
bilateral = bspl.load_file("bilateral.bspl").export("BilateralAgreement")
from BilateralAgreement import Party, CounterParty

# TODO: Define agent addresses
agents = {
    # Define address for party and counterparty
}

# TODO: Define the protocol system
systems = {
    # Configure the bilateral agreement system
}