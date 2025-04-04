from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Timofey", systems, agents)
adapter.load_asl("timofey.asl")

if __name__ == "__main__":
    print("Starting Timofey...")
    adapter.start()
