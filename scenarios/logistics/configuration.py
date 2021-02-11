from protocheck import bspl

logistics = bspl.load_file("logistics.bspl").export("Logistics")
from Logistics import Merchant, Wrapper, Labeler, Packer

with open("/proc/self/cgroup", "r") as cgroups:

    in_docker = "docker" in cgroups.read()

if in_docker:
    config = {
        Merchant: ("merchant", 8000),
        Wrapper: ("wrapper", 8001),
        Labeler: ("labeler", 8002),
        Packer: ("packer", 8003),
    }
else:
    config = {
        Merchant: ("0.0.0.0", 8000),
        Wrapper: ("0.0.0.0", 8001),
        Labeler: ("0.0.0.0", 8002),
        Packer: ("0.0.0.0", 8003),
    }
