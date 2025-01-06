from bspl.adapter import Adapter
from configuration import systems, agents

adapter = Adapter("Wrapper", systems, agents)
adapter.load_asl("wrapper.asl")

if __name__ == "__main__":
    print("Starting Wrapper...")
    adapter.start() 