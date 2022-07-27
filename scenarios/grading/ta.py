import asyncio
import logging
from bspl.adapter import Adapter
from configuration import config, grading, TA

# logging.getLogger("bspl").setLevel(logging.DEBUG)

adapter = Adapter(TA, grading, config, name="Timofey")
adapter.load_asl("timofey.asl")

if __name__ == "__main__":
    print("Starting Timofey...")
    adapter.start()
