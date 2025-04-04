#!/usr/bin/env bash
set -euo pipefail

python lancelot.py &
LANCELOT=$!

python galahad.py &
GALAHAD=$!

python timofey.py &
TIMOFEY=$!

sleep 2
python pnin.py &
PNIN=$!

read -n1 -rsp $'Press any key to stop...\n'

kill $LANCELOT $GALAHAD $TIMOFEY $PNIN
