from protocheck import bspl

prescription = bspl.load_file("prescription.bspl").protocols['Prescription']
prescription_resend = bspl.load_file(
    "prescription-resend.bspl").protocols['Prescription']
prescription_ack = bspl.load_file(
    "prescription-ack.bspl").protocols['Prescription']

Patient = prescription.roles['Patient']
Doctor = prescription.roles['Doctor']
Pharmacist = prescription.roles['Pharmacist']

Complain = prescription.messages['Complain']
Prescribe = prescription.messages['Prescribe']
Filled = prescription.messages['Filled']

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
