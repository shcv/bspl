from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Labeler", systems, agents)
adapter.load_asl("labeler.asl")

if __name__ == "__main__":
    print("Starting Labeler...")
    adapter.start() 