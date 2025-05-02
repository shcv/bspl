#!/usr/bin/env bash

# Start Seller in the background
echo "Starting Seller..."
python seller.py &
SELLER_PID=$!

# Wait a moment for Seller to initialize
sleep 1

# Start Buyer
echo "Starting Buyer..."
python buyer.py &
BUYER_PID=$!

# Wait for user input to stop
read -p "Press any key to stop the agents..."

# Kill the processes
kill $SELLER_PID $BUYER_PID

echo "Agents stopped."
