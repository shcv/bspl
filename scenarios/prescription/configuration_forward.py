from protocheck import bspl

prescription = bspl.load_file(
    "prescription-forward.bspl").protocols['Prescription']

Patient = prescription.roles['Patient']
Doctor = prescription.roles['Doctor']
Pharmacist = prescription.roles['Pharmacist']

Complain = prescription.messages['Complain']
Repeat = prescription.messages['Repeat']
Prescribe = prescription.messages['Prescribe']
Copy = prescription.messages['Copy']
Forward = prescription.messages['Forward']
Filled = prescription.messages['Filled']

Map = {
    "forwards": {
        Complain: (Repeat, 'rID'),
        Prescribe: (Copy, 'copyID'),
        Copy: (Forward, 'fID')
    }
}

with open('/proc/self/cgroup', 'r') as cgroups:
    in_docker = 'docker' in cgroups.read()

if in_docker:
    config = {
        prescription.roles['Patient']: ('patient', 8000),
        prescription.roles['Doctor']: ('doctor', 8000),
        prescription.roles['Pharmacist']: ('pharmacist', 8000),
    }
else:
    config = {
        prescription.roles['Patient']: ('0.0.0.0', 8000),
        prescription.roles['Doctor']: ('0.0.0.0', 8001),
        prescription.roles['Pharmacist']: ('0.0.0.0', 8002),
    }
