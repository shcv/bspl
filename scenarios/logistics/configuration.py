import bspl

logistics = bspl.load_file("logistics.bspl").export("Logistics")
from Logistics import Merchant, Wrapper, Labeler, Packer

agents = {
    "Merchant": [("127.0.0.1", 8000)],
    "Wrapper": [("127.0.0.1", 8001)],
    "Labeler": [("127.0.0.1", 8002)],
    "Packer": [("127.0.0.1", 8003)],
}

systems = {
    "logistics": {
        "protocol": logistics,
        "roles": {
            Merchant: "Merchant",
            Wrapper: "Wrapper",
            Labeler: "Labeler",
            Packer: "Packer",
        },
    },
}
