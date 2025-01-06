from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Packer", systems, agents)
adapter.load_asl("packer.asl")

if __name__ == "__main__":
    print("Starting Packer...")
    adapter.start() 