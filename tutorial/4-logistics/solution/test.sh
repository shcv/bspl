#!/usr/bin/env bash
set -euo pipefail

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments to identify which agent files to use
MERCHANT_SCRIPT="merchant.py"  # Default: solution merchant script
LABELER_SCRIPT="labeler.py"    # Default: solution labeler script
WRAPPER_SCRIPT="wrapper.py"    # Default: solution wrapper script
PACKER_SCRIPT="packer.py"      # Default: solution packer script

# Process command line arguments for agent scripts
while [[ $# -gt 0 ]]; do
  arg="$1"
  # Extract file name and determine agent type from the file name
  filename=$(basename "$arg")
  if [[ "$filename" == *"merchant"* ]]; then
    MERCHANT_SCRIPT="$arg"
    # echo "Using custom merchant script: $MERCHANT_SCRIPT"
  elif [[ "$filename" == *"labeler"* ]]; then
    LABELER_SCRIPT="$arg"
    # echo "Using custom labeler script: $LABELER_SCRIPT"
  elif [[ "$filename" == *"wrapper"* ]]; then
    WRAPPER_SCRIPT="$arg"
    # echo "Using custom wrapper script: $WRAPPER_SCRIPT"
  elif [[ "$filename" == *"packer"* ]]; then
    PACKER_SCRIPT="$arg"
    # echo "Using custom packer script: $PACKER_SCRIPT"
  else
    echo "Warning: Unrecognized agent script: $arg"
  fi
  shift
done

# Create logs directory if it doesn't exist
mkdir -p logs

# Log files
MERCHANT_LOG="logs/merchant.log"
LABELER_LOG="logs/labeler.log"
WRAPPER_LOG="logs/wrapper.log"
PACKER_LOG="logs/packer.log"
COMBINED_LOG="logs/combined.log"

# Kill any existing processes using the ports (in case previous run didn't clean up)
KILLING=false

# Use grep to identify ports being used from configuration 
# Default ports in case no logs exist yet
for port in $(grep -o "Listening on ('localhost', [0-9]*)" logs/*.log 2>/dev/null | grep -o "[0-9]\{4,5\}" || echo "8001 8002 8003 8004"); do
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
rm -f $MERCHANT_LOG $LABELER_LOG $WRAPPER_LOG $PACKER_LOG $COMBINED_LOG

# Create empty log files
touch $MERCHANT_LOG $LABELER_LOG $WRAPPER_LOG $PACKER_LOG $COMBINED_LOG

# Determine if we're running from solution directory or parent directory
# Check if we're inside the solution directory
IS_IN_SOLUTION=false
if [[ "$(basename "$SCRIPT_DIR")" == "solution" ]]; then
  IS_IN_SOLUTION=true
fi

echo "Starting logistics agents..."

# Start Labeler
if [[ "$LABELER_SCRIPT" == /* || "$LABELER_SCRIPT" == ../* || "$LABELER_SCRIPT" == ./* ]]; then
  echo "Starting Labeler from: $LABELER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$LABELER_SCRIPT" > $LABELER_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Labeler from current directory"
    BSPL_ADAPTER_DEBUG=true python "$LABELER_SCRIPT" > $LABELER_LOG 2>&1 &
  else
    echo "Starting Labeler from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$LABELER_SCRIPT" > $LABELER_LOG 2>&1 &
  fi
fi
LABELER_PID=$!

# Start Wrapper
if [[ "$WRAPPER_SCRIPT" == /* || "$WRAPPER_SCRIPT" == ../* || "$WRAPPER_SCRIPT" == ./* ]]; then
  echo "Starting Wrapper from: $WRAPPER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$WRAPPER_SCRIPT" > $WRAPPER_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Wrapper from current directory"
    BSPL_ADAPTER_DEBUG=true python "$WRAPPER_SCRIPT" > $WRAPPER_LOG 2>&1 &
  else
    echo "Starting Wrapper from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$WRAPPER_SCRIPT" > $WRAPPER_LOG 2>&1 &
  fi
fi
WRAPPER_PID=$!

# Start Packer
if [[ "$PACKER_SCRIPT" == /* || "$PACKER_SCRIPT" == ../* || "$PACKER_SCRIPT" == ./* ]]; then
  echo "Starting Packer from: $PACKER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$PACKER_SCRIPT" > $PACKER_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Packer from current directory"
    BSPL_ADAPTER_DEBUG=true python "$PACKER_SCRIPT" > $PACKER_LOG 2>&1 &
  else
    echo "Starting Packer from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$PACKER_SCRIPT" > $PACKER_LOG 2>&1 &
  fi
fi
PACKER_PID=$!

# Wait for support agents to initialize
sleep 1

# Start Merchant (which initiates the protocol)
if [[ "$MERCHANT_SCRIPT" == /* || "$MERCHANT_SCRIPT" == ../* || "$MERCHANT_SCRIPT" == ./* ]]; then
  echo "Starting Merchant from: $MERCHANT_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$MERCHANT_SCRIPT" > $MERCHANT_LOG 2>&1 &
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Merchant from current directory"
    BSPL_ADAPTER_DEBUG=true python "$MERCHANT_SCRIPT" > $MERCHANT_LOG 2>&1 &
  else
    echo "Starting Merchant from solution directory"
    BSPL_ADAPTER_DEBUG=true python "solution/$MERCHANT_SCRIPT" > $MERCHANT_LOG 2>&1 &
  fi
fi
MERCHANT_PID=$!

# Run for 7 seconds to let the protocol execute completely
echo "Running logistics protocol for 7 seconds..."
sleep 7

# Stop all processes
echo "Stopping processes..."
kill $LABELER_PID $WRAPPER_PID $PACKER_PID $MERCHANT_PID 2>/dev/null || true

# Wait for processes to fully terminate
sleep 1

# Combine logs for easier analysis
cat $MERCHANT_LOG $LABELER_LOG $WRAPPER_LOG $PACKER_LOG > $COMBINED_LOG

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

# Test logistics protocol flow
check_pattern "Starting Merchant agent" "Merchant agent started" || ((FAILURES++))
check_pattern "Starting Labeler agent" "Labeler agent started" || ((FAILURES++))
check_pattern "Starting Wrapper agent" "Wrapper agent started" || ((FAILURES++))
check_pattern "Starting Packer agent" "Packer agent started" || ((FAILURES++))

# Check for message transmissions in the debug logs
# Merchant to Labeler communication
check_pattern "Sending.*RequestLabel" "Merchant sent label requests" || ((FAILURES++))
check_pattern "Received message: RequestLabel" "Labeler received label requests" || ((FAILURES++))
check_pattern "Sending.*Labeled" "Labeler sent labels" || ((FAILURES++))
check_pattern "Received message: Labeled" "Packer received labels" || ((FAILURES++))

# Merchant to Wrapper communication
check_pattern "Sending.*RequestWrapping" "Merchant sent wrap requests" || ((FAILURES++))
check_pattern "Received message: RequestWrapping" "Wrapper received wrap requests" || ((FAILURES++))
check_pattern "Sending.*Wrapped" "Wrapper sent wrapped items" || ((FAILURES++))
check_pattern "Received message: Wrapped" "Packer received wrapped items" || ((FAILURES++))

# Packer to Merchant communication
check_pattern "Sending .*Packed" "Packer sent packed confirmations" || ((FAILURES++))
check_pattern "Received message: .*Packed" "Merchant received packed confirmations" || ((FAILURES++))

# Check detailed message parameters
check_pattern "RequestLabel.*orderID.*address" "LabelRequest contains required parameters" || ((FAILURES++))
check_pattern "Labeled.*orderID.*label" "Label contains required parameters" || ((FAILURES++))
check_pattern "RequestWrapping.*itemID.*item" "WrapRequest contains required parameters" || ((FAILURES++))
check_pattern "Wrapped.*itemID.*wrapping" "WrappedItem contains required parameters" || ((FAILURES++))
check_pattern "Packed.*orderID.*itemID.*status" "Packed contains required parameters" || ((FAILURES++))

# Count completed transactions by looking at the protocol level messages
PACKED_ITEMS=$(grep -c "Sending .*Packed" $COMBINED_LOG || echo 0)
LABEL_REQUESTS=$(grep -c "Sending.*RequestLabel" $COMBINED_LOG || echo 0)
WRAP_REQUESTS=$(grep -c "Sending.*RequestWrapping" $COMBINED_LOG || echo 0)

echo "--------------"
echo "Protocol completion summary:"
echo "- Label requests sent: $LABEL_REQUESTS"
echo "- Wrap requests sent: $WRAP_REQUESTS"
echo "- Items packed: $PACKED_ITEMS"

if [ "$PACKED_ITEMS" -ge 1 ]; then
  echo "✅ PASS: At least one item was packed completely"
else
  echo "❌ FAIL: No items were packed"
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