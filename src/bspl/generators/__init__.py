#!/usr/bin/env python3

from . import node_red
from . import asl


class Generate:
    def __init__(self):
        self.node_red = node_red.handle_node_flow
        self.asl = asl.generate_asl
