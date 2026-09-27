#!/bin/bash
cd "$(dirname "$0")"
source ../.venv/bin/activate
python3 era-voice-mac/voice_daemon.py > /tmp/era_voice.log 2>&1 &
python3 era-voice-mac/stt_hacker.py > /tmp/era_stt.log 2>&1 &
