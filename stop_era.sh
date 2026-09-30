#!/bin/bash
VOICE_DIR="$HOME/.gemini/antigravity/era_voice"
echo "🛑 Stopping ERA v3.0..."
pkill -9 -f run_avatar || true
pkill -9 -f voice_daemon.py || true
pkill -9 -f era_brain.py || true
pkill -9 -f stt_hacker.py || true
pkill -9 -f era_hotkeys.py || true
pkill -9 -f afplay || true
pkill -9 -f ERA_Avatar || true
rm -f "$VOICE_DIR/.era.lock"
rm -f "$VOICE_DIR/.era_speaking"
rm -f "$VOICE_DIR/.era_interrupt"
rm -f "$VOICE_DIR/"*.pid
echo "✅ ERA Voice offline. All locks cleared."
