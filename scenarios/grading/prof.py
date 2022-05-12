import bspl
from configuration import config, grading, Prof

adapter = bspl.Adapter(Prof, grading, config, color=bspl.adapter.COLORS[0])
adapter.load_asl("prof.asl")

if __name__ == "__main__":
    print("Starting Prof...")
    adapter.start()
