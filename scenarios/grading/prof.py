from bspl.adapter import Adapter
import bspl.adapter.core
from configuration import config, grading, Prof

adapter = Adapter(Prof, grading, config, color=bspl.adapter.core.COLORS[0], name="Pnin")
adapter.load_asl("pnin.asl")

if __name__ == "__main__":
    print("Starting Pnin...")
    adapter.start()
