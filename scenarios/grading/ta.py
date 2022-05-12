import asyncio
import logging
from bungie import Adapter
from configuration import config, grading, TA

# logging.getLogger("bungie").setLevel(logging.DEBUG)

adapter = Adapter(TA, grading, config)
adapter.load_asl("ta.asl")

if __name__ == "__main__":
    print("Starting TA...")
    adapter.start()
