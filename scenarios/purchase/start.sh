#!/usr/bin/env bash
set -euo pipefail

python seller.py &
SELLER=$!

python shipper.py &
SHIPPER=$!

sleep 2
python buyer.py &
BUYER=$!

read -n1 -rsp $'Press any key to stop...\n'

kill $SELLER $SHIPPER $BUYER
