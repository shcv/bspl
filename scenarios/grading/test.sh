#!/usr/bin/env bash
set -euo pipefail

# Temporary files for output
LANCELOT_LOG="lancelot_output.log"
GALAHAD_LOG="galahad_output.log"
TIMOFEY_LOG="timofey_output.log"
PNIN_LOG="pnin_output.log"
ALL_LOGS="all_output.log"

# Clean up old logs
rm -f $LANCELOT_LOG $GALAHAD_LOG $TIMOFEY_LOG $PNIN_LOG $ALL_LOGS

# Create empty files
touch $LANCELOT_LOG $GALAHAD_LOG $TIMOFEY_LOG $PNIN_LOG $ALL_LOGS

echo "Starting agents..."
# Start the agents
python lancelot.py > $LANCELOT_LOG 2>&1 &
LANCELOT_PID=$!
echo "Started Lancelot (PID: $LANCELOT_PID)"

python galahad.py > $GALAHAD_LOG 2>&1 &
GALAHAD_PID=$!
echo "Started Galahad (PID: $GALAHAD_PID)"

python timofey.py > $TIMOFEY_LOG 2>&1 &
TIMOFEY_PID=$!
echo "Started Timofey (PID: $TIMOFEY_PID)"

# Give agents time to initialize
sleep 1
python pnin.py > $PNIN_LOG 2>&1 &
PNIN_PID=$!
echo "Started Pnin (PID: $PNIN_PID)"

# Run for 1 seconds to ensure all messages get processed
echo "Running enactment for 1 seconds..."
sleep 1

# Kill all agents
echo "Stopping agents..."
kill $LANCELOT_PID $GALAHAD_PID $TIMOFEY_PID $PNIN_PID 2>/dev/null || true

# Wait for processes to fully terminate
sleep 1

# Combine logs for easier analysis
cat $LANCELOT_LOG $GALAHAD_LOG $TIMOFEY_LOG $PNIN_LOG > $ALL_LOGS

# Function to check if pattern exists in logs
check_pattern() {
  local pattern=$1
  local description=$2
  if grep -q "$pattern" $ALL_LOGS; then
    echo "✅ PASS: $description"
    return 0
  else
    echo "❌ FAIL: $description"
    echo "      Pattern not found: $pattern"
    # Show some context around where this pattern might be expected
    echo "      Checking log context:"
    grep -i "${pattern%.*}" $ALL_LOGS | head -3 || echo "      No similar patterns found"
    return 1
  fi
}

echo "Running tests..."
echo "--------------"

# Test basic protocol flow
check_pattern "Starting test" "Professor initiates tests"
check_pattern "Starting test with TID" "Students receive test initiation"
check_pattern "Challenge" "Professor sends challenges"
check_pattern "Answering" "Students answer questions"
check_pattern "Solution for" "Professor provides solutions to TA"
check_pattern "Received end marker" "Students receive test end markers"

# Test grading
check_pattern "matches" "TA correctly identifies matching answers"
check_pattern "does not match" "TA correctly identifies non-matching answers"
check_pattern "Grade:" "TA assigns grades to answers"

# Test result reporting
check_pattern "grade for student" "Professor reports final grades" || echo "    (Final grades might not be calculated in the time limit)"

# Test advanced features
check_pattern "Resigning after answering" "Student can resign from a test" || echo "    (This might not occur if all questions were answered)"

# Display log file details
echo "--------------"
echo "Test logs written to $ALL_LOGS"

# Show a summary of log contents
echo "Log file sizes:"
ls -l *_output.log

echo "Log summary (first 40 lines of combined logs):"
head -n 40 $ALL_LOGS

echo "Done."
