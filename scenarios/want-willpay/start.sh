#!/usr/bin/env bash
set -euo pipefail

python seller.py $1 &
SELLER=$!

sleep 2
python buyer.py $1 &
BUYER=$!

read -n1 -rsp $'Press any key to stop...\n'

kill $SELLER $BUYER
