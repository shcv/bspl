#!/usr/bin/env python3

from bspl.parsers.bspl import load_file

contracting = load_file("../contracting.bspl").export("Contracting")
from Contracting import Customer, Bidder, Accountant, Expert

config = {
    Customer: ("0.0.0.0", 8000),
    Bidder: ("0.0.0.0", 8001),
    Accountant: ("0.0.0.0", 8002),
    Expert: ("0.0.0.0", 8003),
}
