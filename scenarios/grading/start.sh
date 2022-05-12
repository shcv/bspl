#!/usr/bin/env bash
set -euo pipefail

python lancelot.py &
LANCELOT=$!

python galahad.py &
GALAHAD=$!

python ta.py &
TA=$!

sleep 2
python prof.py &
PROF=$!

read -n1 -rsp $'Press any key to stop...\n'

kill $LANCELOT $GALAHAD $TA $PROF
