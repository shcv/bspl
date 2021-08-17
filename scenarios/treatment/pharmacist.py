from bungie import Adapter
from configuration import config, treatment, Pharmacist
import logging

# logging.getLogger("bungie").setLevel(logging.DEBUG)
adapter = Adapter(Pharmacist, treatment, config)
adapter.load_asl("pharmacist.asl")

if __name__ == "__main__":
    print("Starting Pharmacist agent...")
    adapter.start()
