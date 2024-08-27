#!/usr/bin/env bash
set -euo pipefail

python provider1.py &
PROVIDER=$!

python collector1.py &
COLLECTOR=$!

python laboratory1.py &
LABORATORY=$!

sleep 2
python patient1.py &
PATIENT=$!

read -n1 -rsp $'Press any key to stop...\n'

kill $PROVIDER $COLLECTOR $LABORATORY $PATIENT
