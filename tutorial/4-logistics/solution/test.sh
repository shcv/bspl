#!/usr/bin/env bash
set -e
# Safer pipefail for older Bash versions
if [ "${BASH_VERSINFO[0]:-0}" -ge 4 ]; then
  set -o pipefail
fi
set -u

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments to identify which agent files to use
MERCHANT_SCRIPT="merchant.py"  # Default: solution merchant script
LABELER_SCRIPT="labeler.py"    # Default: solution labeler script
WRAPPER_SCRIPT="wrapper.py"    # Default: solution wrapper script
PACKER_SCRIPT="packer.py"      # Default: solution packer script

# Setup PYTHONPATH to ensure modules can be found
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

# Process command line arguments for agent scripts
while [ $# -gt 0 ]; do
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
mkdir -p "$SCRIPT_DIR/logs"

# Log files
MERCHANT_LOG="$SCRIPT_DIR/logs/merchant.log"
LABELER_LOG="$SCRIPT_DIR/logs/labeler.log"
WRAPPER_LOG="$SCRIPT_DIR/logs/wrapper.log"
PACKER_LOG="$SCRIPT_DIR/logs/packer.log"
COMBINED_LOG="$SCRIPT_DIR/logs/combined.log"

# Check for existing processes using the ports (but don't kill them)

# Check for processes using ports that our tests need
DEFAULT_PORTS="8001 8002"
DETECTED_PORTS=""
PORTS_IN_USE=false

# Try to extract ports from logs if they exist
if [ -d "$SCRIPT_DIR/logs" ] && ls "$SCRIPT_DIR/logs"/*.log 1>/dev/null 2>&1; then
    # More compatible grep pattern
    DETECTED_PORTS=$(grep -o "Listening on ('localhost', [0-9]*)" "$SCRIPT_DIR/logs"/*.log 2>/dev/null | 
                     grep -o "[0-9][0-9][0-9][0-9][0-9]\|[0-9][0-9][0-9][0-9]" || echo "")
fi

# Use detected ports or fall back to defaults
PORTS_TO_CHECK=${DETECTED_PORTS:-$DEFAULT_PORTS}

echo "⚙️ Checking for conflicting processes on ports: $PORTS_TO_CHECK"

for port in $PORTS_TO_CHECK; do
    # Try different methods to find processes
    if command -v lsof >/dev/null 2>&1; then
        # If lsof is available (Mac/Linux)
        pid=$(lsof -i:$port -t 2>/dev/null || true)
        if [ -n "$pid" ]; then
            echo "⚠️ WARNING: Port $port is in use by process ID: $pid"
            PORTS_IN_USE=true
        fi
    elif command -v netstat >/dev/null 2>&1; then
        # If netstat is available but not lsof
        if [ "$(uname)" = "Darwin" ]; then
            # Mac OS X style netstat
            pid=$(netstat -anv | grep ".$port " | awk '{print $9}' || true)
        else
            # Linux style netstat
            pid=$(netstat -tulpn 2>/dev/null | grep ":$port " | 
                 grep -o '[0-9]*/[^ ]*' | cut -d/ -f1 || true)
        fi
        
        if [ -n "$pid" ]; then
            echo "⚠️ WARNING: Port $port is in use by process ID: $pid"
            PORTS_IN_USE=true
        fi
    fi
done

# If ports are in use, provide guidance
if $PORTS_IN_USE; then
    echo ""
    echo "⚠️ ========================================================== ⚠️"
    echo "  Some ports required for testing are already in use."
    echo "  This might cause test failures or unexpected behavior."
    echo ""
    echo "  To kill processes using these ports, you can run:"
    echo "  pkill -f 'localhost.*${PORTS_TO_CHECK// /\|localhost.*}'"
    echo "  or for a specific port:"
    echo "  lsof -ti:PORT_NUMBER | xargs kill -9"
    echo "⚠️ ========================================================== ⚠️"
    echo ""
    # Continue tests anyway - user decided not to kill
fi

# Clean up old logs
rm -f $MERCHANT_LOG $LABELER_LOG $WRAPPER_LOG $PACKER_LOG $COMBINED_LOG

# Create empty log files
touch $MERCHANT_LOG $LABELER_LOG $WRAPPER_LOG $PACKER_LOG $COMBINED_LOG

# Clean up any solution/ prefix from script paths
MERCHANT_SCRIPT=$(echo "$MERCHANT_SCRIPT" | sed 's#^solution/##')
LABELER_SCRIPT=$(echo "$LABELER_SCRIPT" | sed 's#^solution/##')
WRAPPER_SCRIPT=$(echo "$WRAPPER_SCRIPT" | sed 's#^solution/##')
PACKER_SCRIPT=$(echo "$PACKER_SCRIPT" | sed 's#^solution/##')

# Save current directory
START_DIR=$(pwd)

# Determine if we're running from solution directory or parent directory
# Check if we're inside the solution directory
IS_IN_SOLUTION=false
if [[ "$(basename "$SCRIPT_DIR")" == "solution" ]]; then
  IS_IN_SOLUTION=true
fi

echo "Starting logistics agents..."

# Start Labeler
if [[ "$LABELER_SCRIPT" == /* ]]; then
  # Absolute path
  echo "Starting Labeler from: $LABELER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$LABELER_SCRIPT" > $LABELER_LOG 2>&1 &
elif [[ "$LABELER_SCRIPT" == ../* || "$LABELER_SCRIPT" == ./* ]]; then
  # Relative path to solution directory
  echo "Starting Labeler from: $LABELER_SCRIPT (relative to $SCRIPT_DIR)"
  cd "$SCRIPT_DIR"
  BSPL_ADAPTER_DEBUG=true python "$LABELER_SCRIPT" > $LABELER_LOG 2>&1 &
  cd - > /dev/null
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Labeler from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$LABELER_SCRIPT" > $LABELER_LOG 2>&1 &
    cd - > /dev/null
  else
    echo "Starting Labeler from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$LABELER_SCRIPT" > $LABELER_LOG 2>&1 &
    cd - > /dev/null
  fi
fi
LABELER_PID=$!

# Start Wrapper
if [[ "$WRAPPER_SCRIPT" == /* ]]; then
  # Absolute path
  echo "Starting Wrapper from: $WRAPPER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$WRAPPER_SCRIPT" > $WRAPPER_LOG 2>&1 &
elif [[ "$WRAPPER_SCRIPT" == ../* || "$WRAPPER_SCRIPT" == ./* ]]; then
  # Relative path to solution directory
  echo "Starting Wrapper from: $WRAPPER_SCRIPT (relative to $SCRIPT_DIR)"
  cd "$SCRIPT_DIR"
  BSPL_ADAPTER_DEBUG=true python "$WRAPPER_SCRIPT" > $WRAPPER_LOG 2>&1 &
  cd - > /dev/null
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Wrapper from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$WRAPPER_SCRIPT" > $WRAPPER_LOG 2>&1 &
    cd - > /dev/null
  else
    echo "Starting Wrapper from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$WRAPPER_SCRIPT" > $WRAPPER_LOG 2>&1 &
    cd - > /dev/null
  fi
fi
WRAPPER_PID=$!

# Start Packer
if [[ "$PACKER_SCRIPT" == /* ]]; then
  # Absolute path
  echo "Starting Packer from: $PACKER_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$PACKER_SCRIPT" > $PACKER_LOG 2>&1 &
elif [[ "$PACKER_SCRIPT" == ../* || "$PACKER_SCRIPT" == ./* ]]; then
  # Relative path to solution directory
  echo "Starting Packer from: $PACKER_SCRIPT (relative to $SCRIPT_DIR)"
  cd "$SCRIPT_DIR"
  BSPL_ADAPTER_DEBUG=true python "$PACKER_SCRIPT" > $PACKER_LOG 2>&1 &
  cd - > /dev/null
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Packer from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$PACKER_SCRIPT" > $PACKER_LOG 2>&1 &
    cd - > /dev/null
  else
    echo "Starting Packer from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$PACKER_SCRIPT" > $PACKER_LOG 2>&1 &
    cd - > /dev/null
  fi
fi
PACKER_PID=$!

# Wait for support agents to initialize
sleep 1

# Start Merchant (which initiates the protocol)
if [[ "$MERCHANT_SCRIPT" == /* ]]; then
  # Absolute path
  echo "Starting Merchant from: $MERCHANT_SCRIPT"
  BSPL_ADAPTER_DEBUG=true python "$MERCHANT_SCRIPT" > $MERCHANT_LOG 2>&1 &
elif [[ "$MERCHANT_SCRIPT" == ../* || "$MERCHANT_SCRIPT" == ./* ]]; then
  # Relative path to solution directory
  echo "Starting Merchant from: $MERCHANT_SCRIPT (relative to $SCRIPT_DIR)"
  cd "$SCRIPT_DIR"
  BSPL_ADAPTER_DEBUG=true python "$MERCHANT_SCRIPT" > $MERCHANT_LOG 2>&1 &
  cd - > /dev/null
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Merchant from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$MERCHANT_SCRIPT" > $MERCHANT_LOG 2>&1 &
    cd - > /dev/null
  else
    echo "Starting Merchant from solution directory"
    cd "$SCRIPT_DIR"
    BSPL_ADAPTER_DEBUG=true python "$MERCHANT_SCRIPT" > $MERCHANT_LOG 2>&1 &
    cd - > /dev/null
  fi
fi
MERCHANT_PID=$!

# Run for 4 seconds to let the protocol execute completely
echo "Running logistics protocol for 4 seconds..."
sleep 4

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
echo "Test logs written to $SCRIPT_DIR/logs/ directory"

# Show a summary of log sizes
echo "Log file sizes:"
ls -l "$SCRIPT_DIR/logs"/*.log

echo "Done."