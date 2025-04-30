"""
Configuration file for the Purchase protocol system.
This file defines the agents and their addresses, and sets up the protocol system.
"""

import bspl
from bspl.parsers.bspl import load_file

# TODO: Load the protocol specification from purchase.bspl

# Example:
# spec = load_file("path-to-protocol.bspl")       # load the file
# protocol_object = spec.export("ProtocolName")     # export protocol as module; also return protocol object
# from ProtocolName import RoleObject, MessageObject        # import relevant role and message objects from protocol

# TODO: Define agent addresses (localhost with different ports)

agents = {
    # Format: "agent_name": [("host", port)],
}

# TODO: Define the Purchase protocol system

systems = {
    # Format: "system_name": {
    #     "protocol": protocol_object,
    #     "roles": {RoleObject: "agent_name"},
    # }
}
