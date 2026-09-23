#!/bin/bash
# macOS / Linux Startup Script for ERA Voice Engine
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "[*] Starting ERA Voice Daemon..."
python3 era-voice-mac/voice_daemon.py
