from protocheck import bspl

spec = bspl.load_file("logistics.bspl")
logistics = spec.protocols['Logistics']

config = {
    logistics.roles['Merchant']: ('merchant', 8000),
    logistics.roles['Wrapper']: ('wrapper', 8001),
    logistics.roles['Labeler']: ('labeler', 8002),
    logistics.roles['Packer']: ('packer', 8003),
}
