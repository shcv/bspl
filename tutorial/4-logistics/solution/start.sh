#!/usr/bin/env bash

# Start each agent in the background and capture its PID
echo "Starting Logistics agents..."

# Start Labeler
echo "Starting Labeler..."
python labeler.py &
LABELER_PID=$!

# Start Wrapper
echo "Starting Wrapper..."
python wrapper.py &
WRAPPER_PID=$!

# Start Packer
echo "Starting Packer..."
python packer.py &
PACKER_PID=$!

# Wait a moment to ensure support agents are ready
sleep 2

# Start Merchant (which initiates the protocol)
echo "Starting Merchant..."
python merchant.py &
MERCHANT_PID=$!

# Define a function to handle clean exit
function cleanup {
    echo "Stopping all agents..."
    kill $LABELER_PID $WRAPPER_PID $PACKER_PID $MERCHANT_PID
    exit 0
}

# Register the cleanup function for SIGINT
trap cleanup SIGINT

echo "All agents are running. Press Ctrl+C to stop."

# Wait for Ctrl+C
while true; do
    sleep 1
done
