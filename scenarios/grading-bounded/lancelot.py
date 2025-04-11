from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Lancelot", systems, agents)
adapter.load_asl("lancelot.asl")

if __name__ == "__main__":
    print("Starting Lancelot...")
    adapter.start()
