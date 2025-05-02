#!/usr/bin/env bash
set -euo pipefail

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments to identify which agent files to use
BUYER_SCRIPT="buyer_enabled.py"  # Default: solution buyer script
SELLER_SCRIPT="seller_enabled.py"  # Default: solution seller script

# Process command line arguments for agent scripts
while [[ $# -gt 0 ]]; do
  arg="$1"
  # Extract file name and determine agent type from the file name
  filename=$(basename "$arg")
  if [[ "$filename" == *"buyer"* ]]; then
    BUYER_SCRIPT="$arg"
    # echo "Using custom buyer script: $BUYER_SCRIPT"
  elif [[ "$filename" == *"seller"* ]]; then
    SELLER_SCRIPT="$arg"
    # echo "Using custom seller script: $SELLER_SCRIPT"
  else
    echo "Warning: Unrecognized agent script: $arg"
  fi
  shift
done

# Create logs directory if it doesn't exist
mkdir -p logs

# Log files
BUYER_LOG="logs/buyer_enabled.log"
SELLER_LOG="logs/seller_enabled.log"
COMBINED_LOG="logs/combined.log"

# Kill any existing processes using the ports (in case previous run didn't clean up)
KILLING=false

# Use grep to identify ports being used from configuration 
# Default ports in case no logs exist yet
for port in $(grep -o "Listening on ('localhost', [0-9]*)" logs/*.log 2>/dev/null | grep -o "[0-9]\{4,5\}" || echo "8001 8002"); do
    pid=$(lsof -i:$port -t 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "Killing process $pid using port $port"
        kill -9 $pid 2>/dev/null || true
        KILLING=true
    fi
done

# Wait for processes to be killed if any were found
if $KILLING; then
  echo "Waiting for processes to terminate..."
  sleep 2
fi

# Clean up old logs
rm -f $BUYER_LOG $SELLER_LOG $COMBINED_LOG

# Create empty log files
touch $BUYER_LOG $SELLER_LOG $COMBINED_LOG

# Determine if we're running from solution directory or parent directory
# Check if we're inside the solution directory
IS_IN_SOLUTION=false
if [[ "$(basename "$SCRIPT_DIR")" == "solution" ]]; then
  IS_IN_SOLUTION=true
fi

# Determine if seller script is a relative path
if [[ "$SELLER_SCRIPT" == /* || "$SELLER_SCRIPT" == ../* || "$SELLER_SCRIPT" == ./* ]]; then
  # Handling absolute or relative path
  echo "Starting Seller (forms-based) from: $SELLER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$SELLER_SCRIPT" > $SELLER_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Seller (forms-based) from current directory"
    BSPL_ADAPTER_DEBUG=true python "$SELLER_SCRIPT" > $SELLER_LOG 2>&1 &
  else
    echo "Starting Seller (forms-based) from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$SELLER_SCRIPT" > $SELLER_LOG 2>&1 &
  fi
fi
SELLER_PID=$!

# Wait for Seller to initialize
sleep 1

# Determine if buyer script is a relative path
if [[ "$BUYER_SCRIPT" == /* || "$BUYER_SCRIPT" == ../* || "$BUYER_SCRIPT" == ./* ]]; then
  # Handling absolute or relative path
  echo "Starting Buyer (forms-based) from: $BUYER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$BUYER_SCRIPT" > $BUYER_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Buyer (forms-based) from current directory"
    BSPL_ADAPTER_DEBUG=true python "$BUYER_SCRIPT" > $BUYER_LOG 2>&1 &
  else
    echo "Starting Buyer (forms-based) from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$BUYER_SCRIPT" > $BUYER_LOG 2>&1 &
  fi
fi
BUYER_PID=$!

# Run for 5 seconds to let the protocol execute completely
echo "Running forms-based purchase protocol for 5 seconds..."
sleep 5

# Stop all processes
echo "Stopping processes..."
kill $SELLER_PID $BUYER_PID 2>/dev/null || true

# Wait for processes to fully terminate
sleep 1

# Combine logs for easier analysis
cat $SELLER_LOG $BUYER_LOG > $COMBINED_LOG

# Function to check if pattern exists in logs
check_pattern() {
  local pattern=$1
  local description=$2
  if grep -q "$pattern" $COMBINED_LOG; then
    echo "✅ PASS: $description"
    return 0
  else
    echo "❌ FAIL: $description"
    echo "      Pattern not found: $pattern"
    # Show some context around where this pattern might be expected
    grep -i "${pattern%.*}" $COMBINED_LOG | head -3 || echo "      No similar patterns found"
    return 1
  fi
}

# Function to check for agent initialization errors
check_agent_errors() {
  if grep -q "KeyError\|ModuleNotFoundError\|ImportError\|AttributeError\|SyntaxError" $COMBINED_LOG; then
    echo "⚠️ WARNING: Detected agent initialization errors:"
    grep -A3 "KeyError\|ModuleNotFoundError\|ImportError\|AttributeError\|SyntaxError" $COMBINED_LOG | head -10
    echo "   Common causes:"
    echo "   - Incomplete configuration.py (missing agent addresses or system configuration)"
    echo "   - Missing or incorrect imports"
    echo "   - Incomplete agent implementation"
    return 1
  fi
  return 0
}

# Initialize failure tracking
FAILURES=0

echo "Running tests..."
echo "--------------"

# Check for initialization errors first
AGENT_ERRORS=0
check_agent_errors || AGENT_ERRORS=1

if [ "$AGENT_ERRORS" -eq 1 ]; then
  echo "⚠️ Agent initialization errors detected - some tests may fail due to incomplete setup"
  echo "--------------"
fi

# Test purchase protocol flow with forms-based approach
check_pattern "Starting Buyer agent.*forms-based" "Buyer agent (forms-based) started" || ((FAILURES++))
check_pattern "Starting Seller agent.*forms-based" "Seller agent (forms-based) started" || ((FAILURES++))

# Check for message transmissions in the debug logs
check_pattern "Received message: .*RFQ" "Seller received RFQ messages" || ((FAILURES++))
check_pattern "Sending .*Quote" "Seller sent Quote messages" || ((FAILURES++))
check_pattern "Received message: .*Quote" "Buyer received Quote messages" || ((FAILURES++))
check_pattern "Sending .*Buy" "Buyer sent Buy messages" || ((FAILURES++))
check_pattern "Sending .*Reject" "Buyer sent Reject messages" || ((FAILURES++))
check_pattern "Received message: .*Buy" "Seller received Buy messages" || ((FAILURES++))
check_pattern "Received message: .*Reject" "Seller received Reject messages" || ((FAILURES++))

# Check detailed message parameters
check_pattern "RFQ.*ID.*item" "RFQ contains required parameters" || ((FAILURES++))
check_pattern "Quote.*ID.*item.*price" "Quote contains required parameters" || ((FAILURES++))
check_pattern "Buy.*ID.*item.*price.*done" "Buy contains required parameters" || ((FAILURES++))
check_pattern "Reject.*ID.*price.*done" "Reject contains required parameters" || ((FAILURES++))

# Count completed transactions by looking at the protocol level messages
ACCEPTED_COUNT=$(grep -c "Sending .*Buy" $COMBINED_LOG || echo 0)
REJECTED_COUNT=$(grep -c "Sending .*Reject" $COMBINED_LOG || echo 0)
TOTAL_COUNT=$((ACCEPTED_COUNT + REJECTED_COUNT))

echo "--------------"
echo "Protocol completion summary:"
echo "- Accepted offers: $ACCEPTED_COUNT"
echo "- Rejected offers: $REJECTED_COUNT"
echo "- Total transactions: $TOTAL_COUNT"

if [ "$TOTAL_COUNT" -ge 1 ]; then
  echo "✅ PASS: At least one transaction completed"
else
  echo "❌ FAIL: No transactions completed"
  ((FAILURES++))
fi

# Print overall test summary
echo "--------------"
echo "Test Summary:"
if [ "$FAILURES" -eq 0 ]; then
  echo "✅ All tests passed!"
else
  echo "❌ $FAILURES test(s) failed"
  exit 1
fi

# Display log file details
echo "--------------"
echo "Test logs written to logs/ directory"

# Show a summary of log sizes
echo "Log file sizes:"
ls -l logs/*.log

echo "Done."