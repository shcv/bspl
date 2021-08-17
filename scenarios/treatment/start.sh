#!/usr/bin/env bash
set -euo pipefail

python doctor.py &
DOCTOR=$!

python pharmacist.py &
PHARMACIST=$!

sleep 2
python patient.py &
PATIENT=$!

read -n1 -rsp $'Press any key to stop...\n'

kill $PATIENT $DOCTOR $PHARMACIST
