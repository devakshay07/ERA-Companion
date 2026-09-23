#!/bin/bash
mkdir -p ~/.gemini/antigravity/era_voice

cat << 'PYEOF' > ~/.gemini/antigravity/era_voice/voice_daemon.py
import time
import json
import subprocess
import os
import re
import glob

def get_latest_transcript():
    search_pattern = os.path.expanduser("~/.gemini/antigravity/brain/*/.system_generated/logs/transcript.jsonl")
    files = glob.glob(search_pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def clean_text_for_speech(text):
    text = re.sub(r'```.*?```', ' [code block] ', text, flags=re.DOTALL)
    text = re.sub(r'`.*?`', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'https?://[^\s]+', ' [link] ', text)
    return text.strip()

def speak(text):
    cleaned = clean_text_for_speech(text)
    if not cleaned:
        return
    lock_file = os.path.expanduser("~/.gemini/antigravity/era_voice/.era.lock")
    try:
        with open(lock_file, "w") as f:
            f.write("1")
        subprocess.run(["say", "-v", "Samantha", cleaned])
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)

def main():
    print("Global ERA Voice Daemon activated.")
    current_transcript = None
    f = None
    try:
        while True:
            latest = get_latest_transcript()
            if not latest:
                time.sleep(2)
                continue
            if latest != current_transcript:
                print(f"Tracking new chat session: {latest}")
                if f: f.close()
                current_transcript = latest
                f = open(current_transcript, 'r')
                f.seek(0, 2)
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            try:
                data = json.loads(line)
                if data.get("source") == "MODEL" and data.get("type") == "PLANNER_RESPONSE":
                    content = data.get("content", "")
                    if content: speak(content)
            except Exception as e: pass
    except KeyboardInterrupt:
        if f: f.close()

if __name__ == "__main__":
    main()
PYEOF

cp stt_hacker.py ~/.gemini/antigravity/era_voice/stt_hacker.py
sed -i '' "s|~/.gemini/antigravity/era_voice/.era.lock|~/.gemini/antigravity/era_voice/.era.lock|g" ~/.gemini/antigravity/era_voice/stt_hacker.py

echo "Installation complete."
echo "To run the global voice daemon anywhere, open a terminal and run:"
echo "python3 ~/.gemini/antigravity/era_voice/voice_daemon.py"
echo ""
echo "To run the global listener anywhere, open a terminal and run:"
echo "python3 ~/.gemini/antigravity/era_voice/stt_hacker.py"
