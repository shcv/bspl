#!/usr/bin/env bash
set -euo pipefail

# This script is a wrapper around the solution test script
# It will run the current directory's agent files
# using the solution's test harness

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOLUTION_TEST="$SCRIPT_DIR/solution/test.sh"

# Check if the solution test script exists
if [ ! -f "$SOLUTION_TEST" ]; then
  echo "Error: solution/test.sh does not exist at $SOLUTION_TEST"
  exit 1
fi

# Check if current agent files exist
MERCHANT_FILE="$(pwd)/merchant.py"
LABELER_FILE="$(pwd)/labeler.py"
PACKER_FILE="$(pwd)/packer.py"
WRAPPER_FILE="$(pwd)/wrapper.py"
LOGISTICS_FILE="$(pwd)/logistics.bspl"

if [ ! -f "$MERCHANT_FILE" ]; then
  echo "Error: $MERCHANT_FILE does not exist"
  exit 1
fi

if [ ! -f "$LABELER_FILE" ]; then
  echo "Error: $LABELER_FILE does not exist"
  exit 1
fi

if [ ! -f "$PACKER_FILE" ]; then
  echo "Error: $PACKER_FILE does not exist"
  exit 1
fi

if [ ! -f "$WRAPPER_FILE" ]; then
  echo "Error: $WRAPPER_FILE does not exist"
  exit 1
fi

if [ ! -f "$LOGISTICS_FILE" ]; then
  echo "Error: $LOGISTICS_FILE does not exist"
  exit 1
fi

# Run the solution test script with the current directory's files
echo "Running solution test script with local implementation files..."

# Call the solution's test script with our files
"$SOLUTION_TEST" "$MERCHANT_FILE" "$LABELER_FILE" "$PACKER_FILE" "$WRAPPER_FILE"