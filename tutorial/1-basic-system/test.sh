#!/usr/bin/env bash
set -euo pipefail

# This script is a wrapper around the solution test script
# It will run the current directory's buyer.py and seller.py files
# using the solution's test harness

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOLUTION_TEST="$SCRIPT_DIR/solution/test.sh"

# Check if the solution test script exists
if [ ! -f "$SOLUTION_TEST" ]; then
  echo "Error: solution/test.sh does not exist at $SOLUTION_TEST"
  exit 1
fi

# Check if current buyer.py and seller.py exist
BUYER_FILE="$(pwd)/buyer.py"
SELLER_FILE="$(pwd)/seller.py"
PURCHASE_FILE="$(pwd)/purchase.bspl"

if [ ! -f "$BUYER_FILE" ]; then
  echo "Error: $BUYER_FILE does not exist"
  exit 1
fi

if [ ! -f "$SELLER_FILE" ]; then
  echo "Error: $SELLER_FILE does not exist"
  exit 1
fi

if [ ! -f "$PURCHASE_FILE" ]; then
  echo "Error: $PURCHASE_FILE does not exist"
  exit 1
fi

# Run the solution test script with the current directory's files
echo "Running solution test script with local implementation files..."

# Call the solution's test script with our files
"$SOLUTION_TEST" "$BUYER_FILE" "$SELLER_FILE"
