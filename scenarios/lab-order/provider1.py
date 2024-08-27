#!/usr/bin/env python3

from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Provider-1", systems, agents, trace=True)
adapter.load_asl("Provider-1.asl")
# bspl.adapter.jason.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Starting Provider-1...")
    adapter.start()
