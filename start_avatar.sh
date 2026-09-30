#!/bin/bash
WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
echo "[*] Launching ERA 3D Avatar Engine..."

pkill -9 -f ERA_Avatar
pkill -9 -f run_avatar

PYTHON_BIN="python3"
if [ -f "$WORKSPACE/.venv/bin/python" ]; then PYTHON_BIN="$WORKSPACE/.venv/bin/python"; fi
if [ -f "$WORKSPACE/../.venv/bin/python" ]; then PYTHON_BIN="$WORKSPACE/../.venv/bin/python"; fi

cd "$WORKSPACE"
"$PYTHON_BIN" "$WORKSPACE/era_hotkeys.py" > /tmp/era_hotkeys.log 2>&1 &

cd "$WORKSPACE/era-avatar"
"$PYTHON_BIN" run_avatar.py > /tmp/era_avatar_start.log 2>&1 &
