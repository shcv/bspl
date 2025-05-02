#!/usr/bin/env bash
set -euo pipefail

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments to identify which agent files to use
PARTY_SCRIPT="party.py"  # Default: solution party script
COUNTERPARTY_SCRIPT="counterparty.py"  # Default: solution counterparty script

# Process command line arguments for agent scripts
while [[ $# -gt 0 ]]; do
  arg="$1"
  # Extract file name and determine agent type from the file name
  filename=$(basename "$arg")
  if [[ "$filename" == *"party"* && "$filename" != *"counter"* ]]; then
    PARTY_SCRIPT="$arg"
    # echo "Using custom party script: $PARTY_SCRIPT"
  elif [[ "$filename" == *"counterparty"* ]]; then
    COUNTERPARTY_SCRIPT="$arg"
    # echo "Using custom counterparty script: $COUNTERPARTY_SCRIPT"
  else
    echo "Warning: Unrecognized agent script: $arg"
  fi
  shift
done

# Create logs directory if it doesn't exist
mkdir -p logs

# Log files
PARTY_LOG="logs/party.log"
COUNTERPARTY_LOG="logs/counterparty.log"
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
rm -f $PARTY_LOG $COUNTERPARTY_LOG $COMBINED_LOG

# Create empty log files
touch $PARTY_LOG $COUNTERPARTY_LOG $COMBINED_LOG

# Determine if we're running from solution directory or parent directory
# Check if we're inside the solution directory
IS_IN_SOLUTION=false
if [[ "$(basename "$SCRIPT_DIR")" == "solution" ]]; then
  IS_IN_SOLUTION=true
fi

# Determine if counterparty script is a relative path
if [[ "$COUNTERPARTY_SCRIPT" == /* || "$COUNTERPARTY_SCRIPT" == ../* || "$COUNTERPARTY_SCRIPT" == ./* ]]; then
  # Handling absolute or relative path
  echo "Starting CounterParty from: $COUNTERPARTY_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$COUNTERPARTY_SCRIPT" > $COUNTERPARTY_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting CounterParty from current directory"
    BSPL_ADAPTER_DEBUG=true python "$COUNTERPARTY_SCRIPT" > $COUNTERPARTY_LOG 2>&1 &
  else
    echo "Starting CounterParty from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$COUNTERPARTY_SCRIPT" > $COUNTERPARTY_LOG 2>&1 &
  fi
fi
COUNTERPARTY_PID=$!

# Wait for CounterParty to initialize
sleep 1

# Determine if party script is a relative path
if [[ "$PARTY_SCRIPT" == /* || "$PARTY_SCRIPT" == ../* || "$PARTY_SCRIPT" == ./* ]]; then
  # Handling absolute or relative path
  echo "Starting Party from: $PARTY_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$PARTY_SCRIPT" > $PARTY_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Party from current directory"
    BSPL_ADAPTER_DEBUG=true python "$PARTY_SCRIPT" > $PARTY_LOG 2>&1 &
  else
    echo "Starting Party from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$PARTY_SCRIPT" > $PARTY_LOG 2>&1 &
  fi
fi
PARTY_PID=$!

# Run for 12 seconds to ensure we see all protocol patterns
# (including withdrawals which happen after 10 seconds)
echo "Running bilateral agreement protocol for 12 seconds..."
sleep 12

# Stop all processes
echo "Stopping processes..."
kill $COUNTERPARTY_PID $PARTY_PID 2>/dev/null || true

# Wait for processes to fully terminate
sleep 1

# Combine logs for easier analysis
cat $PARTY_LOG $COUNTERPARTY_LOG > $COMBINED_LOG

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

# Test bilateral agreement protocol flow (all paths)
check_pattern "Starting Party agent" "Party agent started" || ((FAILURES++))
check_pattern "Starting CounterParty agent" "CounterParty agent started" || ((FAILURES++))

# Check for message transmissions in the debug logs
check_pattern "Received message: .*Request" "CounterParty received Request messages" || ((FAILURES++))
check_pattern "Sending .*Propose" "Party sent Propose messages" || ((FAILURES++))
check_pattern "Received message: .*Propose" "CounterParty received Propose messages" || ((FAILURES++))
check_pattern "Sending .*Accept" "CounterParty sent Accept messages" || ((FAILURES++))
check_pattern "Sending .*Reject" "CounterParty sent Reject messages" || ((FAILURES++))
check_pattern "Received message: .*Accept" "Party received Accept messages" || ((FAILURES++))
check_pattern "Received message: .*Reject" "Party received Reject messages" || ((FAILURES++))
check_pattern "Sending .*Execute" "Party sent Execute messages" || ((FAILURES++))
check_pattern "Sending .*Acknowledge" "Party sent Acknowledge messages" || ((FAILURES++))
check_pattern "Received message: .*Execute" "CounterParty received Execute messages" || ((FAILURES++))
check_pattern "Received message: .*Acknowledge" "CounterParty received Acknowledge messages" || ((FAILURES++))
check_pattern "Sending .*Withdraw" "Party sent Withdraw messages" || ((FAILURES++))
check_pattern "Received message: .*Withdraw" "CounterParty received Withdraw messages" || ((FAILURES++))

# Check detailed message parameters
check_pattern "Request.*ID.*details" "Request contains required parameters" || ((FAILURES++))
check_pattern "Propose.*ID.*details.*terms" "Propose contains required parameters" || ((FAILURES++))
check_pattern "Accept.*ID.*terms.*status" "Accept contains required parameters" || ((FAILURES++))
check_pattern "Reject.*ID.*status" "Reject contains required parameters" || ((FAILURES++))
check_pattern "Execute.*ID.*outcome" "Execute contains required parameters" || ((FAILURES++))
check_pattern "Acknowledge.*ID" "Acknowledge contains required parameters" || ((FAILURES++))
check_pattern "Withdraw.*ID" "Withdraw contains required parameters" || ((FAILURES++))

# Count completed transactions by looking at the protocol level messages
EXECUTED_COUNT=$(grep -c "Sending .*Execute" $COMBINED_LOG || echo 0)
REJECTED_COUNT=$(grep -c "Sending .*Acknowledge" $COMBINED_LOG || echo 0)
WITHDRAWN_COUNT=$(grep -c "Sending .*Withdraw" $COMBINED_LOG || echo 0)
TOTAL_COUNT=$((EXECUTED_COUNT + REJECTED_COUNT + WITHDRAWN_COUNT))

echo "--------------"
echo "Protocol completion summary:"
echo "- Executed agreements: $EXECUTED_COUNT"
echo "- Rejected proposals: $REJECTED_COUNT"
echo "- Withdrawn proposals: $WITHDRAWN_COUNT"
echo "- Total completed: $TOTAL_COUNT"

if [ "$TOTAL_COUNT" -ge 1 ]; then
  echo "✅ PASS: At least one agreement completed"
else
  echo "❌ FAIL: No agreements completed"
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