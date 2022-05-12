import bungie
from configuration import config, grading, Prof

adapter = bungie.Adapter(Prof, grading, config, color=bungie.adapter.COLORS[0])
adapter.load_asl("prof.asl")

if __name__ == "__main__":
    print("Starting Prof...")
    adapter.start()
