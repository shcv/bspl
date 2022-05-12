import asyncio
import logging
from bungie import Adapter
from configuration import config, grading, Student

Galahad = ("0.0.0.0", 8011)
config[Student] = Galahad

adapter = Adapter(Student, grading, config)
adapter.load_asl("galahad.asl")

if __name__ == "__main__":
    print("Starting Galahad...")
    adapter.start()
