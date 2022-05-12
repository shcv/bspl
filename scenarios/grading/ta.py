import asyncio
import logging
from bspl.adapter import Adapter
from configuration import config, grading, TA

# logging.getLogger("bspl").setLevel(logging.DEBUG)

adapter = Adapter(TA, grading, config)
adapter.load_asl("ta.asl")

if __name__ == "__main__":
    print("Starting TA...")
    adapter.start()
