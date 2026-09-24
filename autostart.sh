#!/bin/bash
cd "/Users/akshaybhagat/Documents/ERA'S ARENA"

echo "Initializing ERA Voice Engine..."
./start_era.sh

echo "Launching Visual Avatar (Detached)..."
nohup ./start_avatar.sh > /tmp/era_avatar.log 2>&1 &

echo "ERA is now running in the background! You can safely close this terminal."
