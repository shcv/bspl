import bspl

create_order = bspl.load_file("simplified-lab-order.bspl").export("CreateOrder")
from CreateOrder import Patient, Provider, Collector, Laboratory

agents = {
    "Patient-1": [("127.0.0.1", 8000)],
    "Provider-1": [("127.0.0.1", 8001)],
    "Collector-1": [("127.0.0.1", 8002)],
    "Laboratory-1": [("127.0.0.1", 8003)],
}

systems = {
    "main": {
        "protocol": create_order,
        "roles": {
            Patient: "Patient-1",
            Provider: "Provider-1",
            Collector: "Collector-1",
            Laboratory: "Laboratory-1",
        },
    }
}
