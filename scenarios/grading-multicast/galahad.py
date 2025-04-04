from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Galahad", systems, agents)
adapter.load_asl("galahad.asl")

if __name__ == "__main__":
    print("Starting Galahad...")
    adapter.start()
