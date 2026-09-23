#!/bin/bash
# macOS / Linux Startup Script for ERA 3D Avatar
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "[*] Starting ERA 3D Avatar Engine..."
python3 era-avatar/run_avatar.py
