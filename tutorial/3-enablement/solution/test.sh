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
BUYER_SCRIPT="buyer_enabled.py"  # Default: solution buyer script
SELLER_SCRIPT="seller_enabled.py"  # Default: solution seller script

# Setup PYTHONPATH to ensure modules can be found
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

# Process command line arguments for agent scripts
while [ $# -gt 0 ]; do
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
mkdir -p "$SCRIPT_DIR/logs"

# Log files
BUYER_LOG="$SCRIPT_DIR/logs/buyer_enabled.log"
SELLER_LOG="$SCRIPT_DIR/logs/seller_enabled.log"
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
rm -f $BUYER_LOG $SELLER_LOG $COMBINED_LOG

# Create empty log files
touch $BUYER_LOG $SELLER_LOG $COMBINED_LOG

# Clean up any solution/ prefix from script paths
BUYER_SCRIPT=$(echo "$BUYER_SCRIPT" | sed 's#^solution/##')
SELLER_SCRIPT=$(echo "$SELLER_SCRIPT" | sed 's#^solution/##')

# Save current directory
START_DIR=$(pwd)

# Determine if we're running from solution directory or parent directory
# Check if we're inside the solution directory
IS_IN_SOLUTION=false
if [[ "$(basename "$SCRIPT_DIR")" == "solution" ]]; then
  IS_IN_SOLUTION=true
fi

# Determine if seller script is a relative path
if [[ "$SELLER_SCRIPT" == /* ]]; then
  # Absolute path
  echo "Starting Seller (forms-based) from: $SELLER_SCRIPT"
  SCRIPT_DIR_PATH=$(dirname "$SELLER_SCRIPT")
  export PYTHONPATH="$SCRIPT_DIR_PATH:${PYTHONPATH:-}"
  BSPL_ADAPTER_DEBUG=true python "$SELLER_SCRIPT" > $SELLER_LOG 2>&1 &
elif [[ "$SELLER_SCRIPT" == ../* || "$SELLER_SCRIPT" == ./* ]]; then
  # Relative path to solution directory
  echo "Starting Seller (forms-based) from: $SELLER_SCRIPT (relative to $SCRIPT_DIR)"
  cd "$SCRIPT_DIR"
  export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
  BSPL_ADAPTER_DEBUG=true python "$SELLER_SCRIPT" > $SELLER_LOG 2>&1 &
  cd - > /dev/null
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Seller (forms-based) from solution directory"
    cd "$SCRIPT_DIR"
    export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
    BSPL_ADAPTER_DEBUG=true python "$SELLER_SCRIPT" > $SELLER_LOG 2>&1 &
    cd - > /dev/null
  else
    echo "Starting Seller (forms-based) from solution directory"
    cd "$SCRIPT_DIR"
    export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
    BSPL_ADAPTER_DEBUG=true python "$SELLER_SCRIPT" > $SELLER_LOG 2>&1 &
    cd - > /dev/null
  fi
fi
SELLER_PID=$!

# Wait for Seller to initialize
sleep 1

# Determine if buyer script is a relative path
if [[ "$BUYER_SCRIPT" == /* ]]; then
  # Absolute path
  echo "Starting Buyer (forms-based) from: $BUYER_SCRIPT"
  SCRIPT_DIR_PATH=$(dirname "$BUYER_SCRIPT")
  export PYTHONPATH="$SCRIPT_DIR_PATH:${PYTHONPATH:-}"
  BSPL_ADAPTER_DEBUG=true python "$BUYER_SCRIPT" > $BUYER_LOG 2>&1 &
elif [[ "$BUYER_SCRIPT" == ../* || "$BUYER_SCRIPT" == ./* ]]; then
  # Relative path to solution directory
  echo "Starting Buyer (forms-based) from: $BUYER_SCRIPT (relative to $SCRIPT_DIR)"
  cd "$SCRIPT_DIR"
  export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
  BSPL_ADAPTER_DEBUG=true python "$BUYER_SCRIPT" > $BUYER_LOG 2>&1 &
  cd - > /dev/null
else
  # Handle both running from parent or solution directory
  if $IS_IN_SOLUTION; then
    echo "Starting Buyer (forms-based) from solution directory"
    cd "$SCRIPT_DIR"
    export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
    BSPL_ADAPTER_DEBUG=true python "$BUYER_SCRIPT" > $BUYER_LOG 2>&1 &
    cd - > /dev/null
  else
    echo "Starting Buyer (forms-based) from solution directory"
    cd "$SCRIPT_DIR"
    export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
    BSPL_ADAPTER_DEBUG=true python "$BUYER_SCRIPT" > $BUYER_LOG 2>&1 &
    cd - > /dev/null
  fi
fi
BUYER_PID=$!

# Run for 3 seconds to let the protocol execute completely
echo "Running forms-based purchase protocol for 3 seconds..."
sleep 3

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
echo "Test logs written to $SCRIPT_DIR/logs/ directory"

# Show a summary of log sizes
echo "Log file sizes:"
ls -l "$SCRIPT_DIR/logs"/*.log

echo "Done."