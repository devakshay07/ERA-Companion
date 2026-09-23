# ERA Audio Protocol 🎙️

A fully local, hands-free, headless voice assistant and system-wide dictation macro for macOS. 

No cloud constraints. No corporate safety bumpers. Just pure, unadulterated hardware control.

## What is this?
This repo contains the background daemons that power **ERA**. 
It turns your Mac into a continuous-listening, smart-speaking terminal that types what you say into whatever window is active, and reads back AI responses using Microsoft's neural TTS engine. 

- **Global Voice Macro:** Speak anywhere (Chrome, Xcode, Terminal) and it types for you and hits Enter.
- **Neural TTS:** Instant, zero-latency cloud TTS using `edge-tts` (Sonia's British voice, by default).
- **Auto-Muting Lockfiles:** OS-level locks prevent the STT from hearing the TTS (no feedback loops).
- **Silent Background Daemons:** Runs completely headless via `nohup`.

## Installation

1. Create a Python virtual environment and install the dependencies:
```bash
uv venv
uv pip install mlx-whisper sounddevice edge-tts
```
2. Run the installer:
```bash
./install_voice.sh
```

## Usage

Use the provided shell scripts (which can easily be bound to Apple Shortcuts or Automator):

- **Start Systems:** `./start_era.sh`
- **Kill Systems:** `./stop_era.sh`

> **Note:** Requires macOS Accessibility and Microphone permissions to be granted to your Terminal/Shortcuts app.

*Built by ERA.*
