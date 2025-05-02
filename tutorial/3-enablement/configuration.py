"""
Configuration file for the Purchase protocol system.
"""

import bspl

# Load the protocol and export it
purchase = bspl.load_file("purchase.bspl").export("Purchase")
from Purchase import B, S

# TODO: Define agent addresses
agents = {
    # Define addresses for buyer and seller
}

# TODO: Define the protocol system
systems = {
    # Configure the purchase system
}