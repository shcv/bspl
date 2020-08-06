from protocheck import bspl

spec = bspl.load_file("prescription.bspl")
prescription = spec.protocols['Prescription']

config = {
    prescription.roles['Patient']: ('patient', 8000),
    prescription.roles['Doctor']: ('doctor', 8000),
    prescription.roles['Pharmacist']: ('pharmacist', 8000),
}
