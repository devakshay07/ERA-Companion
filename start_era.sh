#!/bin/bash
set -e
WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
echo "🚀 Starting ERA Voice Engine..."
"$WORKSPACE/stop_era.sh" 2>/dev/null || true
sleep 1
# Assuming .venv is in the repo root or parent. We'll use python3 or the repo's .venv if it exists.
PYTHON_BIN="python3"
if [ -f "$WORKSPACE/.venv/bin/python" ]; then PYTHON_BIN="$WORKSPACE/.venv/bin/python"; fi
if [ -f "$WORKSPACE/../.venv/bin/python" ]; then PYTHON_BIN="$WORKSPACE/../.venv/bin/python"; fi

nohup "$PYTHON_BIN" "$WORKSPACE/era-voice-mac/voice_daemon.py" > /tmp/era_tts.log 2>&1 &
nohup "$PYTHON_BIN" "$WORKSPACE/era-voice-mac/stt_hacker.py" > /tmp/era_stt.log 2>&1 &
