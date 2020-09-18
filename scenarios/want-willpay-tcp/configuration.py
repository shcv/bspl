from protocheck import bspl

spec = bspl.load_file("want-willpay.bspl")
protocol = spec.protocols['Want-Willpay']

Buyer = protocol.roles['Buyer']
Seller = protocol.roles['Seller']

Want = protocol.messages['Want']
WillPay = protocol.messages['WillPay']

config = {
    Buyer: ('buyer', 8000),
    Seller: ('seller', 8001),
}
