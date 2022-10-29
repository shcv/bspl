#!/usr/bin/env bash
set -euo pipefail

for i in 0 1 2; do
    python seller.py "S${i}" &
    SELLER[i]=$!
done

python approver.py &
APPROVER=$!

sleep 1
python buyer.py &
BUYER=$!

read -n1 -rsp $'Press any key to stop...\n'

kill "${SELLER[@]}" $BUYER $APPROVER
