from bungie import Adapter

from configuration import (
    config,
    treatment,
    Doctor,
)

adapter = Adapter(Doctor, treatment, config)
adapter.load_asl("doctor.asl")

if __name__ == "__main__":
    print("Starting Doctor...")
    adapter.start()
