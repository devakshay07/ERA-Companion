@echo off
:: Windows Startup Script for ERA 3D Avatar
cd /d "%~dp0"

IF NOT EXIST ".venv\" (
    echo [*] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)

echo [*] Starting ERA 3D Avatar Engine...
python era-avatar\run_avatar.py
