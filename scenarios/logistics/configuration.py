from protocheck import bspl

spec = bspl.load_file("logistics.bspl")
logistics = spec.protocols['Logistics']

with open('/proc/self/cgroup', 'r') as cgroups:
    in_docker = 'docker' in cgroups.read()

if in_docker:
    config = {
        logistics.roles['Merchant']: ('merchant', 8000),
        logistics.roles['Wrapper']: ('wrapper', 8001),
        logistics.roles['Labeler']: ('labeler', 8002),
        logistics.roles['Packer']: ('packer', 8003),
    }
else:
    config = {
        logistics.roles['Merchant']: ('0.0.0.0', 8000),
        logistics.roles['Wrapper']: ('0.0.0.0', 8001),
        logistics.roles['Labeler']: ('0.0.0.0', 8002),
        logistics.roles['Packer']: ('0.0.0.0', 8003),
    }
