@echo off
:: Windows Startup Script for ERA Voice Engine
cd /d "%~dp0"

IF NOT EXIST ".venv\" (
    echo [*] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)

echo [*] Starting ERA Voice Daemon...
python era-voice-mac\voice_daemon.py
