#!/bin/bash
# ERA Voice v3.0 — Deploy Script

set -e

VOICE_DIR="$HOME/.gemini/antigravity/era_voice"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"

echo "🔧 ERA Voice v3.0 — Installing..."

# Kill old daemons
pkill -f voice_daemon.py 2>/dev/null || true
pkill -f stt_hacker.py 2>/dev/null || true
sleep 1

# Clean stale flags
rm -f "$VOICE_DIR/.era.lock"
rm -f "$VOICE_DIR/.era_speaking"
rm -f "$VOICE_DIR/.era_interrupt"

# Copy new scripts
mkdir -p "$VOICE_DIR"
cp "$SCRIPT_DIR/voice_daemon.py" "$VOICE_DIR/voice_daemon.py"
cp "$SCRIPT_DIR/stt_hacker.py" "$VOICE_DIR/stt_hacker.py"

echo "✅ Scripts deployed to $VOICE_DIR"

# Start daemons
echo "🚀 Starting TTS daemon..."
nohup "$WORKSPACE/.venv/bin/python" "$VOICE_DIR/voice_daemon.py" > /tmp/era_tts.log 2>&1 &
echo $! > "$VOICE_DIR/voice_daemon.pid"

echo "🚀 Starting STT daemon..."
nohup "$WORKSPACE/.venv/bin/python" "$VOICE_DIR/stt_hacker.py" > /tmp/era_stt.log 2>&1 &
echo $! > "$VOICE_DIR/stt_hacker.pid"

echo ""
echo "═══════════════════════════════════════════"
echo "  ERA Voice v3.0 — ONLINE"
echo "  TTS PID: $(cat $VOICE_DIR/voice_daemon.pid)"
echo "  STT PID: $(cat $VOICE_DIR/stt_hacker.pid)"
echo "═══════════════════════════════════════════"
