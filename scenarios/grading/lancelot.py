import asyncio
import logging
from bspl import Adapter
from configuration import config, grading, Student

Lancelot = ("0.0.0.0", 8010)
config[Student] = Lancelot
adapter = Adapter(Student, grading, config)
adapter.load_asl("lancelot.asl")

if __name__ == "__main__":
    print("Starting Lancelot...")
    adapter.start()
