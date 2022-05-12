from bspl.adapter import Adapter
import bspl.adapter.core
from configuration import config, grading, Prof

adapter = Adapter(Prof, grading, config, color=bspl.adapter.core.COLORS[0])
adapter.load_asl("prof.asl")

if __name__ == "__main__":
    print("Starting Prof...")
    adapter.start()
