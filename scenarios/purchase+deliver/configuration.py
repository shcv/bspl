import bspl

purchase = bspl.load_file("../../samples/trade-finance/purchase.bspl").export("Purchase")
deliver = bspl.load_file("deliver.bspl").export("Deliver")
from Purchase import Buyer, Seller
from Deliver import Sender, Shipper, Recipient

B = ("0.0.0.0", 8000)
S = [("0.0.0.0", 8001 + i) for i in range(3)]
Sh = ("0.0.0.0", 8010)

systems = {}
for i, s in enumerate(S):
    systems[2 * i] = {
        "protocol": purchase,
        "roles": {Buyer: "B", Seller: f"S{i}"},
        "agents": {"B": B, f"S{i}": S[i]},
    }
    systems[2 * i + 1] = {
        "protocol": deliver,
        "roles": {Sender: f"S{i}", Shipper: "Sh", Recipient: "B"},
        "agents": {f"S{i}": S[i], "B": B, "Sh": Sh},
    }
