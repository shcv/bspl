#!/usr/bin/env python3

from bspl.adapter import Adapter
import bspl.adapter.core
from configuration import systems, agents

adapter = Adapter("Laboratory-1", systems, agents, trace=True)
adapter.load_asl("Laboratory-1.asl")

if __name__ == "__main__":
    print("Starting Laboratory-1...")
    adapter.start()
