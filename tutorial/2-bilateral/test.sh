#!/usr/bin/env bash
set -euo pipefail

# This script is a wrapper around the solution test script
# It will run the current directory's party.py and counterparty.py files
# using the solution's test harness

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOLUTION_TEST="$SCRIPT_DIR/solution/test.sh"

# Check if the solution test script exists
if [ ! -f "$SOLUTION_TEST" ]; then
  echo "Error: solution/test.sh does not exist at $SOLUTION_TEST"
  exit 1
fi

# Check if current party.py and counterparty.py exist
PARTY_FILE="$(pwd)/party.py"
COUNTERPARTY_FILE="$(pwd)/counterparty.py"
BILATERAL_FILE="$(pwd)/bilateral.bspl"

if [ ! -f "$PARTY_FILE" ]; then
  echo "Error: $PARTY_FILE does not exist"
  exit 1
fi

if [ ! -f "$COUNTERPARTY_FILE" ]; then
  echo "Error: $COUNTERPARTY_FILE does not exist"
  exit 1
fi

if [ ! -f "$BILATERAL_FILE" ]; then
  echo "Error: $BILATERAL_FILE does not exist"
  exit 1
fi

# Run the solution test script with the current directory's files
echo "Running solution test script with local implementation files..."

# Call the solution's test script with our files
"$SOLUTION_TEST" "$PARTY_FILE" "$COUNTERPARTY_FILE"