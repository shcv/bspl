#!/usr/bin/env bash

# Start CounterParty in the background
echo "Starting CounterParty..."
python counterparty.py &
COUNTERPARTY_PID=$!

# Wait a moment for CounterParty to initialize
sleep 1

# Start Party
echo "Starting Party..."
python party.py &
PARTY_PID=$!

echo "Both agents are running. Press Ctrl+C to stop."

# Define a function to handle clean exit
function cleanup {
    echo "Stopping agents..."
    kill $COUNTERPARTY_PID $PARTY_PID
    exit 0
}

# Register the cleanup function for SIGINT
trap cleanup SIGINT

# Wait for Ctrl+C
while true; do
    sleep 1
done
