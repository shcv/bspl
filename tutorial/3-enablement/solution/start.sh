#!/usr/bin/env bash

# Start Seller in the background
echo "Starting Seller (Forms-based)..."
python seller_enabled.py &
SELLER_PID=$!

# Wait a moment for Seller to initialize
sleep 1

# Start Buyer
echo "Starting Buyer (Forms-based)..."
python buyer_enabled.py &
BUYER_PID=$!

# Define a function to handle clean exit
function cleanup {
    echo "Stopping agents..."
    kill $SELLER_PID $BUYER_PID
    exit 0
}

# Register the cleanup function for SIGINT
trap cleanup SIGINT

echo "Both agents are running. Press Ctrl+C to stop."

# Wait for Ctrl+C
while true; do
    sleep 1
done
