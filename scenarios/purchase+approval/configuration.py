import bspl

purchase = bspl.load_file("purchase.bspl").export("Purchase")
approval = bspl.load_file("approval.bspl").export("Approval")
from Purchase import Buyer, Seller
from Approval import Requester, Approver

agents = {
    "Bob": [("127.0.0.1", 1111), ("127.0.0.2", 1111)],
    "Alice": [("127.0.1.1", 1111)],
}
for i in range(3):
    agents[f"S{i}"] = [(f"127.0.2.{i}", 1111)]

systems = {}
for i in range(3):
    systems[2 * i] = {
        "protocol": purchase,
        "roles": {Buyer: "Bob", Seller: f"S{i}"},
    }
    systems[2 * i + 1] = {
        "protocol": approval,
        "roles": {Requester: "Bob", Approver: "Alice"},
    }
