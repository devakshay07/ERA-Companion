
import fcntl
import sys
import os
try:
    _singleton_lock_file = open('/tmp/era_hotkeys_daemon.lock', 'w')
    fcntl.lockf(_singleton_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("Instance already running. Exiting strict singleton lock.")
    sys.exit(0)


import os
import subprocess
from pynput import keyboard

def notify(title, msg, sound):
    script = f'display notification "{msg}" with title "{title}" sound name "{sound}"'
    subprocess.run(["osascript", "-e", script])

def toggle_mic():
    lock = '/tmp/era_mic.lock'
    if os.path.exists(lock):
        os.remove(lock)
        notify("ERA Override", "Microphone is LIVE", "Ping")
    else:
        with open(lock, 'w') as f: f.write('1')
        notify("ERA Override", "Microphone is MUTED", "Basso")


def ptt_press():
    with open('/tmp/era_ptt.lock', 'w') as f: f.write('1')

def ptt_release():
    if os.path.exists('/tmp/era_ptt.lock'):
        os.remove('/tmp/era_ptt.lock')

def toggle_speaker():
    lock = '/tmp/era_speaker.lock'
    if os.path.exists(lock):
        os.remove(lock)
        notify("ERA Override", "Speaker is LIVE", "Ping")
    else:
        with open(lock, 'w') as f: f.write('1')
        notify("ERA Override", "Speaker is MUTED", "Basso")

COMBINATIONS = [
    {
        "keys": [
            {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode(char='m')},
            {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode(char='M')}
        ],
        "command": toggle_mic,
    },
    {
        "keys": [
            {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode(char='s')},
            {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode(char='S')}
        ],
        "command": toggle_speaker,
    },
    {
        "keys": [
            {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode(char='v')},
            {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode(char='V')}
        ],
        "command": ptt_press,
        "release_command": ptt_release
    }
]

current_keys = set()

def on_press(key):
    current_keys.add(key)
    for combo in COMBINATIONS:
        for keyset in combo["keys"]:
            if keyset.issubset(current_keys):
                combo["command"]()
                # Remove the char to prevent rapid firing
                for k in keyset:
                    if isinstance(k, keyboard.KeyCode):
                        current_keys.remove(k)
                        break


def on_release(key):
    try:
        # Check if we are releasing a PTT key
        if key == keyboard.KeyCode(char='v') or key == keyboard.KeyCode(char='V'):
            for combo in COMBINATIONS:
                if 'release_command' in combo:
                    combo['release_command']()
        current_keys.remove(key)
    except KeyError:
        pass


print("ERA Hotkeys active. Press Cmd+Shift+M (Mic) or Cmd+Shift+S (Speaker).")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
