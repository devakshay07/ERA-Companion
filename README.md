# ERA Companion Engine 👾

A lightweight, local-first, voice-activated 3D desktop companion avatar engine. Built for performance and extreme low latency.

Features two standalone modules that communicate via a zero-latency file-state bridge:
1. **ERA Voice Daemon:** A high-speed TTS/STT loop powered by `edge-tts` and local Whisper/SpeechRecognition.
2. **ERA Avatar Engine:** A completely transparent, borderless WebGL 3D renderer running in `pywebview`, featuring physics, procedurally driven lip-sync, and high-contrast cinematic lighting.

## 🚀 Installation & Usage

ERA requires **Python 3.10+**.

The repository includes auto-setup scripts for both Windows and macOS/Linux. Simply double-click the script or run it in your terminal. It will automatically build the virtual environment and install dependencies.

### 1. Launch the 3D Avatar
- **Windows:** Run `start_avatar.bat`
- **macOS/Linux:** Run `./start_avatar.sh`

### 2. Launch the Voice Engine (Optional)
If you want the avatar to speak and lip-sync with you:
- **Windows:** Run `start_voice.bat`
- **macOS/Linux:** Run `./start_voice.sh`

## 🛠 Architecture

- **Rendering:** Three.js + WebGL. Loads `.glb` models natively.
- **Window Management:** `pywebview` in frameless, transparent mode.
- **IPC (Inter-Process Communication):** The Voice Daemon writes a `.era_speaking` flag to the user's home directory. The WebGL engine polls a local `state.json` bridged by the Python HTTP server to animate the jaw bone synchronously with the audio stream.

## 🖼 Customizing the Model

To swap the avatar, replace the `.glb` file located in `era-avatar/new_model/H4054EZGP96J1HOA08T7Z836N.glb` with your own animated `.glb`. 
Ensure your model is scaled properly. The engine auto-scales any GLB to 1.6 meters dynamically on load.

## 📝 License
MIT License. Feel free to fork, hack, and modify.

## 🤝 Credits
Built collaboratively by Akshay Bhagat and ERA (Google DeepMind Agentic Systems).
