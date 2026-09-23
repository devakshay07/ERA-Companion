#!/bin/bash
BASE_DIR="$HOME/.gemini/antigravity/era_voice"

if [ -f "$BASE_DIR/voice_daemon.pid" ]; then
    kill $(cat "$BASE_DIR/voice_daemon.pid") 2>/dev/null
    rm "$BASE_DIR/voice_daemon.pid"
fi

if [ -f "$BASE_DIR/stt_hacker.pid" ]; then
    kill $(cat "$BASE_DIR/stt_hacker.pid") 2>/dev/null
    rm "$BASE_DIR/stt_hacker.pid"
fi

# Fallback kill just in case
pkill -f voice_daemon.py 2>/dev/null
pkill -f stt_hacker.py 2>/dev/null

echo "ERA audio systems are OFFLINE."
