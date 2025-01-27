from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Merchant", systems, agents)
adapter.load_asl("merchant.asl")

if __name__ == "__main__":
    print("Starting Merchant...")
    adapter.start() 