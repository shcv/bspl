from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Pnin", systems, agents)
adapter.load_asl("pnin.asl")

if __name__ == "__main__":
    print("Starting Pnin...")
    adapter.start()
