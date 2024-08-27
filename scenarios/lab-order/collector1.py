#!/usr/bin/env python3

from bspl.adapter import Adapter
import bspl.adapter.core
from configuration import systems, agents

adapter = Adapter("Collector-1", systems, agents, trace=True)
adapter.load_asl("Collector-1.asl")

if __name__ == "__main__":
    print("Starting Collector-1...")
    adapter.start()
