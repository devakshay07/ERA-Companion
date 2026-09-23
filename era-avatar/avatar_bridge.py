import os
import json
import time

VOICE_DIR = os.path.expanduser("~/.gemini/antigravity/era_voice")
SPEAKING_FLAG = os.path.join(VOICE_DIR, ".era_speaking")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

def main():
    print("[Bridge] Online. Monitoring voice engine...")
    last_state = None
    
    # Initialize state file
    with open(STATE_FILE, 'w') as f:
        json.dump({"speaking": False}, f)
        
    while True:
        try:
            is_speaking = os.path.exists(SPEAKING_FLAG)
            
            if is_speaking != last_state:
                with open(STATE_FILE, 'w') as f:
                    json.dump({"speaking": is_speaking}, f)
                last_state = is_speaking
                
            # Check 10 times a second (extremely lightweight)
            time.sleep(0.1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == '__main__':
    main()
