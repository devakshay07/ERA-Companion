#!/bin/bash
# Install using uv pip instead of python pip
uv pip install edge-tts --python "$PWD/.venv"

# Restart the daemon
kill $(cat ~/.gemini/antigravity/era_voice/voice_daemon.pid) 2>/dev/null
pkill -f voice_daemon.py 2>/dev/null
nohup "$PWD/.venv/bin/python" ~/.gemini/antigravity/era_voice/voice_daemon.py > /tmp/era_voice.log 2>&1 &
echo $! > ~/.gemini/antigravity/era_voice/voice_daemon.pid

echo "Edge-TTS installed using uv. Daemon restarted."
