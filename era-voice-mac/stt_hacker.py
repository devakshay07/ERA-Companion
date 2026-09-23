#!/usr/bin/env python3
"""
ERA STT Hacker v3.0 — Voice-Activated Interrupt System
- Transcribes speech and types it into the active window
- During TTS playback: runs a high-threshold VAD to detect user voice
- If user speaks during TTS: fires an interrupt signal to kill TTS instantly
- Anti-hallucination filters built-in
"""
import os
import sys
import time
import queue
import numpy as np
import sounddevice as sd
import mlx_whisper
import subprocess

def log_info(msg, **kwargs):
    kw_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[INFO] {msg} {kw_str}", flush=True)

def log_error(msg, **kwargs):
    kw_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[ERROR] {msg} {kw_str}", file=sys.stderr, flush=True)

SAMPLE_RATE = 16000

# Normal listening threshold (quiet room)
THRESHOLD_NORMAL = 0.015

# High threshold during TTS playback
# 0.03 was too low (triggered by your speakers). 0.08 was too high.
# Setting to the Goldilocks zone: 0.06
THRESHOLD_INTERRUPT = 0.06

# How long the user must speak to trigger an interrupt (seconds)
# 0.15s requires a solid syllable, preventing sharp speaker pops from triggering it
INTERRUPT_SUSTAIN = 0.15

# Silence duration before we stop recording and transcribe
SILENCE_DURATION = 0.8

VOICE_DIR = os.path.expanduser("~/.gemini/antigravity/era_voice")
SPEAKING_FLAG = os.path.join(VOICE_DIR, ".era_speaking")
INTERRUPT_FLAG = os.path.join(VOICE_DIR, ".era_interrupt")
LOCK_FILE = os.path.join(VOICE_DIR, ".era.lock")

audio_queue = queue.Queue()


def audio_callback(indata, frames, time_info, status):
    """Sounddevice callback — pushes raw audio chunks to the queue."""
    audio_queue.put(indata.copy())


def is_tts_speaking() -> bool:
    """Check if the TTS daemon is currently playing audio."""
    return os.path.exists(SPEAKING_FLAG)


def fire_interrupt():
    """Signal the TTS daemon to immediately stop speaking."""
    try:
        with open(INTERRUPT_FLAG, "w") as f:
            f.write("1")
        log_info("interrupt_fired")
    except Exception as e:
        log_error("interrupt_fire_failed", error=str(e))


def type_text_applescript(text: str):
    """Type text into the currently active window using AppleScript."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
    tell application "System Events"
        keystroke "{escaped}"
        key code 36
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], timeout=5)
    except Exception as e:
        log_error("applescript_failed", error=str(e))


def is_hallucination(text: str) -> bool:
    """Detect common Whisper hallucination patterns."""
    t = text.lower().strip()

    # Known garbage phrases
    garbage = [
        "subscribe", "thanks for watching", "thank you for watching",
        "amara.org", "transcribed by", "copyright", "by subscrip",
        "i'm going to", "the end", "bye bye", "see you next time",
        "please like", "please subscribe"
    ]
    for phrase in garbage:
        if phrase in t:
            return True

    # Repetition detector
    words = t.split()
    if len(words) > 6:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            return True

    # Too short to be meaningful
    if len(t) < 3:
        return True

    # Starts with bracket (Whisper metadata)
    if t.startswith("[") or t.startswith("("):
        return True

    return False


def monitor_for_interrupt():
    """
    During TTS playback, wait for a volume spike.
    If detected, record until brief silence, transcribe it,
    and ONLY kill TTS if it contains specific kill words.
    """
    log_info("interrupt_monitor_active")
    
    spike_buffer = []
    
    # 1. Wait for a volume spike
    while is_tts_speaking():
        try:
            chunk = audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue
            
        volume = np.max(np.abs(chunk))
        if volume > THRESHOLD_INTERRUPT:
            spike_buffer.append(chunk)
            break
            
    if not is_tts_speaking() or not spike_buffer:
        return
        
    # 2. Record until brief silence
    silence_start = None
    while is_tts_speaking():
        try:
            chunk = audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue
            
        spike_buffer.append(chunk)
        volume = np.max(np.abs(chunk))
        
        if volume < THRESHOLD_INTERRUPT:
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start > 0.4:  # Short silence
                break
        else:
            silence_start = None
            
    # 3. Transcribe and check for kill words
    audio_np = np.concatenate(spike_buffer, axis=0).flatten()
    if len(audio_np) < SAMPLE_RATE * 0.2:
        return
        
    try:
        log_info("checking_interrupt_words...")
        result = mlx_whisper.transcribe(
            audio_np,
            path_or_hf_repo="mlx-community/whisper-tiny"
        )
        text = result["text"].lower().strip()
        log_info("interrupt_heard", text=text)
        
        # --- ECHO CANCELLATION HACK ---
        # Read what TTS is currently speaking
        current_sentence = ""
        try:
            with open(os.path.join(VOICE_DIR, ".era_current_sentence"), "r") as f:
                current_sentence = f.read().strip()
        except:
            pass
            
        import difflib
        import string
        
        # Clean punctuation for comparison
        clean_text = text.translate(str.maketrans('', '', string.punctuation))
        clean_tts = current_sentence.translate(str.maketrans('', '', string.punctuation))
        
        # If the recognized text is a direct substring of what TTS is saying,
        # or heavily overlaps, it's just the speaker echo.
        if clean_text in clean_tts:
            log_info("echo_detected_and_ignored", text=clean_text)
            return
            
        # Or if it's very similar (fuzzy match)
        similarity = difflib.SequenceMatcher(None, clean_text, clean_tts).ratio()
        if similarity > 0.5 or (len(clean_text) > 3 and difflib.SequenceMatcher(None, clean_text, clean_tts).find_longest_match(0, len(clean_text), 0, len(clean_tts)).size > len(clean_text) * 0.7):
            log_info("fuzzy_echo_detected_and_ignored", text=clean_text, ratio=similarity)
            return
        # ------------------------------
        
        kill_words = ["stop", "shut", "quiet", "enough", "cancel", "halt", "wait"]
        
        if any(w in text for w in kill_words):
            log_info("kill_word_detected", triggering_word=text)
            fire_interrupt()
            
            # CRITICAL: Drain the queue and sleep so the word 
            # doesn't get typed into the chat by the main loop.
            time.sleep(0.5)
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                except queue.Empty:
                    break
            time.sleep(0.5)
            return
        else:
            log_info("ignored_noise", text=text)
            
    except Exception as e:
        log_error("interrupt_transcribe_error", error=str(e))


def record_and_transcribe():
    """Record audio until silence, then transcribe with Whisper."""
    audio_buffer = []

    # Wait for voice activity
    while True:
        # If TTS starts speaking while we're waiting, switch to interrupt mode
        if is_tts_speaking():
            monitor_for_interrupt()
            continue

        try:
            chunk = audio_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        volume = np.max(np.abs(chunk))
        if volume > THRESHOLD_NORMAL:
            audio_buffer.append(chunk)
            break

    # Record until silence
    silence_start = None
    while True:
        # Check if TTS started during our recording (shouldn't happen, but safety)
        if is_tts_speaking():
            log_info("tts_started_during_recording_aborting")
            return None

        try:
            chunk = audio_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        audio_buffer.append(chunk)
        volume = np.max(np.abs(chunk))

        if volume < THRESHOLD_NORMAL:
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start > SILENCE_DURATION:
                break
        else:
            silence_start = None

    # Concatenate and transcribe
    audio_np = np.concatenate(audio_buffer, axis=0).flatten()
    if len(audio_np) < SAMPLE_RATE * 0.3:  # less than 300ms of audio
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

        return text

    except Exception as e:
        log_error("transcription_failed", error=str(e))
        return None


def main():
    log_info("stt_hacker_v3_online")

    # Cleanup stale interrupt flag
    try:
        os.remove(INTERRUPT_FLAG)
    except FileNotFoundError:
        pass

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=audio_callback
    )

    with stream:
        while True:
            try:
                # If TTS is speaking, run interrupt monitor instead of transcribing
                if is_tts_speaking():
                    monitor_for_interrupt()
                    continue

                text = record_and_transcribe()
                if text:
                    log_info("typing", text=text[:50])
                    type_text_applescript(text)

            except KeyboardInterrupt:
                log_info("stt_shutdown")
                break
            except Exception as e:
                log_error("main_loop_error", error=str(e))
                time.sleep(1)


if __name__ == "__main__":
    main()
