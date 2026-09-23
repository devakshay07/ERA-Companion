#!/bin/bash
# Use the python from our virtual environment that has mlx-whisper installed
PYTHON_EXEC="/Users/akshaybhagat/Documents/ERA'S ARENA/.venv/bin/python"
BASE_DIR="$HOME/.gemini/antigravity/era_voice"

# Start Voice Daemon
nohup "$PYTHON_EXEC" "$BASE_DIR/voice_daemon.py" > /tmp/era_voice.log 2>&1 &
echo $! > "$BASE_DIR/voice_daemon.pid"

# Start STT Listener
nohup "$PYTHON_EXEC" "$BASE_DIR/stt_hacker.py" > /tmp/era_stt.log 2>&1 &
echo $! > "$BASE_DIR/stt_hacker.pid"

echo "ERA audio systems are ONLINE."
