#!/usr/bin/env python3
"""
ERA Voice Daemon v3.0 — Streaming Sentence-Level TTS
- Splits responses into sentences and speaks them one at a time
- Supports voice-based interruption mid-speech
- Pre-buffers next sentence audio while current one plays
"""
import os
import re
import sys
import json
import glob
import time
import signal
import tempfile
import asyncio
import subprocess

def log_info(msg, **kwargs):
    kw_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[INFO] {msg} {kw_str}", flush=True)

def log_error(msg, **kwargs):
    kw_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[ERROR] {msg} {kw_str}", file=sys.stderr, flush=True)

VOICE = "en-GB-SoniaNeural"
VOICE_DIR = os.path.expanduser("~/.gemini/antigravity/era_voice")
LOCK_FILE = os.path.join(VOICE_DIR, ".era.lock")
SPEAKING_FLAG = os.path.join(VOICE_DIR, ".era_speaking")
INTERRUPT_FLAG = os.path.join(VOICE_DIR, ".era_interrupt")

os.makedirs(VOICE_DIR, exist_ok=True)


def get_latest_transcript():
    """Find the most recently modified transcript across all workspaces."""
    pattern = os.path.expanduser(
        "~/.gemini/antigravity/brain/*/.system_generated/logs/transcript.jsonl"
    )
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def split_into_sentences(text: str) -> list[str]:
    """Split text into speakable sentence chunks."""
    # Strip markdown artifacts
    text = re.sub(r'```[\s\S]*?```', '', text)           # code blocks
    text = re.sub(r'`[^`]+`', '', text)                  # inline code
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text) # links
    text = re.sub(r'[#*_~>|]', '', text)                 # markdown chars
    text = re.sub(r'\n{2,}', '. ', text)                 # paragraph breaks
    text = re.sub(r'\n', ' ', text)                      # single newlines
    text = re.sub(r'\s+', ' ', text).strip()              # collapse spaces

    # Split on sentence boundaries
    raw = re.split(r'(?<=[.!?])\s+', text)

    sentences = []
    for s in raw:
        s = s.strip()
        if len(s) > 5:  # skip tiny fragments
            sentences.append(s)

    return sentences


async def generate_audio(sentence: str, output_path: str):
    """Generate TTS audio for a single sentence using edge-tts."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(sentence, VOICE)
        await communicate.save(output_path)
        return True
    except Exception as e:
        log_error("tts_generation_failed", sentence=sentence[:30], error=str(e))
        return False


def play_audio(audio_path: str) -> subprocess.Popen | None:
    """Play audio file using macOS afplay. Returns the process handle."""
    try:
        proc = subprocess.Popen(
            ["afplay", audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return proc
    except Exception as e:
        log_error("audio_play_failed", error=str(e))
        return None


def set_speaking(active: bool):
    """Signal to STT whether we are currently speaking."""
    if active:
        with open(SPEAKING_FLAG, "w") as f:
            f.write("1")
        with open(LOCK_FILE, "w") as f:
            f.write("1")
    else:
        for f in [SPEAKING_FLAG, LOCK_FILE]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass


def check_interrupt() -> bool:
    """Check if the STT daemon has signaled a voice interrupt."""
    if os.path.exists(INTERRUPT_FLAG):
        try:
            os.remove(INTERRUPT_FLAG)
        except FileNotFoundError:
            pass
        return True
    return False


async def speak_response(text: str):
    """Stream-speak a full response by pre-buffering the next sentence."""
    sentences = split_into_sentences(text)
    if not sentences:
        return

    log_info("speaking_start", sentence_count=len(sentences))
    set_speaking(True)

    check_interrupt()  # clear stale
    tmp_dir = tempfile.mkdtemp(prefix="era_tts_")
    audio_queue = asyncio.Queue()
    generated_files = []
    
    interrupt_event = asyncio.Event()

    async def generator():
        """Generates mp3s in the background and queues them."""
        for i, sentence in enumerate(sentences):
            if interrupt_event.is_set():
                break
            audio_path = os.path.join(tmp_dir, f"sentence_{i}.mp3")
            success = await generate_audio(sentence, audio_path)
            if success:
                generated_files.append(audio_path)
                await audio_queue.put((audio_path, sentence))
        await audio_queue.put(None)  # EOF marker

    async def player():
        """Plays mp3s from the queue consecutively."""
        while True:
            if interrupt_event.is_set():
                break
            
            # Wait for next audio chunk
            item = await audio_queue.get()
            if item is None:
                break
                
            audio_path, current_sentence_text = item
            
            # Write current sentence to file for STT to read (Echo Cancellation)
            try:
                with open(os.path.join(VOICE_DIR, ".era_current_sentence"), "w") as f:
                    f.write(current_sentence_text.lower())
            except:
                pass
                
            if check_interrupt():
                interrupt_event.set()
                break

            proc = play_audio(audio_path)
            if proc is None:
                continue

            # Wait for playback, polling for interrupt
            while proc.poll() is None:
                if check_interrupt():
                    interrupt_event.set()
                    proc.kill()
                    proc.wait()
                    return
                await asyncio.sleep(0.05)

    try:
        # Run generator and player concurrently
        gen_task = asyncio.create_task(generator())
        play_task = asyncio.create_task(player())
        
        await asyncio.gather(gen_task, play_task)
    except Exception as e:
        log_error("speaking_error", error=str(e))
    finally:
        set_speaking(False)
        for f in generated_files:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
        try:
            os.rmdir(tmp_dir)
        except Exception:
            pass
        log_info("speaking_done")


def tail_transcript():
    """Main loop: tail the latest transcript and speak MODEL responses."""
    log_info("voice_daemon_v3_online")

    current_transcript = None
    f = None
    last_spoken_line = -1

    while True:
        try:
            latest = get_latest_transcript()
            if not latest:
                time.sleep(2)
                continue

            # Switch to new transcript if workspace changed
            if latest != current_transcript:
                if f:
                    f.close()
                current_transcript = latest
                f = open(current_transcript, "r")
                # Seek to end so we only speak NEW responses
                f.seek(0, 2)
                last_spoken_line = -1
                log_info("tracking_transcript", path=current_transcript)

            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Only speak MODEL planner responses
            if data.get("source") != "MODEL":
                continue
            if data.get("type") != "PLANNER_RESPONSE":
                continue

            content = data.get("content", "")
            if not content or len(content.strip()) < 10:
                continue

            step = data.get("step_index", 0)
            if step <= last_spoken_line:
                continue

            last_spoken_line = step

            # Add a small delay to let the lockfile from previous cycle clear
            time.sleep(0.3)

            log_info("new_response_detected", step=step, length=len(content))
            asyncio.run(speak_response(content))

        except Exception as e:
            log_error("main_loop_error", error=str(e))
            time.sleep(2)


def main():
    # Cleanup stale flags on startup
    for flag in [SPEAKING_FLAG, LOCK_FILE, INTERRUPT_FLAG]:
        try:
            os.remove(flag)
        except FileNotFoundError:
            pass

    tail_transcript()


if __name__ == "__main__":
    main()
