#!/usr/bin/env python3
import os
import sys
import time
import queue
import json
import subprocess
import numpy as np
import sounddevice as sd
import mlx_whisper

VOICE_DIR = os.path.expanduser("~/.gemini/antigravity/era_voice")
os.makedirs(VOICE_DIR, exist_ok=True)
PTT_LOCK = '/tmp/era_ptt.lock'

SAMPLE_RATE = 16000
audio_queue = queue.Queue()

def log_info(msg, **kwargs):
    kw_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[INFO] {msg} {kw_str}", flush=True)

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(indata.copy())

def type_text_applescript(text):
    escaped_text = text.replace('"', '\"')
    script = f'''
    tell application "System Events"
        set activeBundle to bundle identifier of first application process whose frontmost is true
    end tell
    
    tell application "Antigravity" to activate
    delay 0.15
    tell application "System Events"
        keystroke "{escaped_text}"
        delay 0.1
        key code 36
        delay 0.1
        key code 36 using command down
    end tell
    
    delay 0.1
    if activeBundle is not "com.google.antigravity" then
        do shell script "open -b " & activeBundle
    end if
    '''
    subprocess.run(["osascript", "-e", script])

def is_hallucination(text: str) -> bool:
    t = text.lower().strip()
    if len(t) < 3: return True
    if len(set(t)) < 3: return True
    vowels = set("aeiouy")
    if not any(v in t for v in vowels): return True
    hallucinations = [
        "watching", "subscribe", "thank you", "amara.org",
        "bye", "okay", "test", "subtitle"
    ]
    if t in hallucinations: return True
    return False

def fire_interrupt():
    try:
        with open(os.path.join(VOICE_DIR, '.era_interrupt'), 'w') as f:
            f.write('1')
        subprocess.run(["pkill", "-9", "-f", "afplay"]) # Ensure immediate audio death
    except: pass

def record_and_transcribe():
    # Wait for PTT to be pressed
    while not os.path.exists(PTT_LOCK):
        time.sleep(0.05)
        # Flush queue while waiting
        while not audio_queue.empty():
            audio_queue.get_nowait()
            
    log_info("ptt_pressed_recording")
    fire_interrupt()
    audio_buffer = []
    
    # Record as long as PTT is held
    while os.path.exists(PTT_LOCK):
        try:
            chunk = audio_queue.get(timeout=0.1)
            audio_buffer.append(chunk)
        except queue.Empty:
            pass

    log_info("ptt_released_transcribing")
    
    if not audio_buffer:
        return None
        
    audio_np = np.concatenate(audio_buffer, axis=0).flatten()
    if len(audio_np) < SAMPLE_RATE * 0.3:
        return None

    try:
        result = mlx_whisper.transcribe(
            audio_np,
            path_or_hf_repo="mlx-community/whisper-tiny"
        )
        text = result["text"].strip()

        if not text or is_hallucination(text):
            if text:
                log_info("hallucination_blocked", text=text[:50])
            return None

        # Write subtitle for UI
        try:
            with open(os.path.join(VOICE_DIR, '.era_subtitle'), 'w') as f:
                f.write(text)
        except: pass

        return text
    except Exception as e:
        log_info(f"transcription_failed: {e}")
        return None

def main():
    import fcntl
    try:
        _singleton = open('/tmp/era_stt_hacker.lock', 'w')
        fcntl.lockf(_singleton, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit(0)
        
    log_info("stt_hacker_v4_ptt_only_online")

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=audio_callback)
    with stream:
        while True:
            try:
                text = record_and_transcribe()
                if text:
                    log_info("typing", text=text[:50])
                    type_text_applescript(text)
            except KeyboardInterrupt:
                break
            except Exception as e:
                time.sleep(1)

if __name__ == '__main__':
    main()
