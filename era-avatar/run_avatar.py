
import fcntl
import sys
import os
try:
    _singleton_lock_file = open('/tmp/era_run_avatar.lock', 'w')
    fcntl.lockf(_singleton_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("Instance already running. Exiting strict singleton lock.")
    sys.exit(0)

import os
import threading
import http.server
import socketserver
import time
import json
import subprocess

VOICE_DIR = os.path.expanduser("~/.gemini/antigravity/era_voice")
SPEAKING_FLAG = os.path.join(VOICE_DIR, ".era_speaking")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

def start_server_and_bridge():
    PORT = 8000
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
            
        def do_GET(self):
            if self.path.startswith('/toggle_mic'):
                lock_file = '/tmp/era_mic.lock'
                muted = False
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                else:
                    with open(lock_file, 'w') as f: f.write('1')
                    muted = True
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'muted': muted}).encode())
                return
            elif self.path.startswith('/toggle_speaker'):
                lock_file = '/tmp/era_speaker.lock'
                muted = False
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                else:
                    with open(lock_file, 'w') as f: f.write('1')
                    muted = True
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'muted': muted}).encode())
                return
            elif self.path.startswith('/status'):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'mic_muted': os.path.exists('/tmp/era_mic.lock'),
                    'speaker_muted': os.path.exists('/tmp/era_speaker.lock')
                }).encode())
                return
                
            return super().do_GET()
            
    socketserver.TCPServer.allow_reuse_address = True
    
    def serve():
        try:
            with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
                httpd.serve_forever()
        except OSError:
            pass
            
    threading.Thread(target=serve, daemon=True).start()
    
    # State Bridge Loop
    LISTENING_FLAG = os.path.join(VOICE_DIR, ".era_listening")
    SUBTITLE_FLAG = os.path.join(VOICE_DIR, ".era_subtitle")
    
    with open(STATE_FILE, 'w') as f:
        json.dump({"speaking": False, "listening": False, "emotion": "neutral", "subtitle": ""}, f)
        
    subtitle_text = ""
    subtitle_time = 0
        
    last_state = None
    current_emotion = "neutral"
    
    while True:
        try:
            if os.path.exists(SPEAKING_FLAG):
                try:
                    with open(SPEAKING_FLAG, 'r') as sf:
                        read_emotion = sf.read().strip()
                        if read_emotion: 
                            current_emotion = read_emotion
                except:
                    pass
                is_speaking = True
            else:
                is_speaking = False
                
            is_listening = False # Ripped out active listening
            
            # Read subtitle
            if os.path.exists(SUBTITLE_FLAG):
                try:
                    with open(SUBTITLE_FLAG, 'r') as sf:
                        subtitle_text = sf.read().strip()
                    os.remove(SUBTITLE_FLAG)
                    subtitle_time = time.time()
                except:
                    pass
            
            # Clear subtitle after 5 seconds
            if subtitle_text and (time.time() - subtitle_time > 5.0):
                subtitle_text = ""
                
            current_state = {"speaking": is_speaking, "listening": is_listening, "emotion": current_emotion, "subtitle": subtitle_text}
            if current_state != last_state:
                with open(STATE_FILE, 'w') as f:
                    json.dump(current_state, f)
                last_state = current_state
            time.sleep(0.05)
        except Exception:
            time.sleep(0.5)

if __name__ == '__main__':
    # Start the HTTP server to serve the assets
    server_thread = threading.Thread(target=start_server_and_bridge, daemon=True)
    server_thread.start()

    print("ERA HTTP backend started. Launching native Swift shell...")
    # Launch the native Swift app that actually renders the UI
    subprocess.call(["/Users/akshaybhagat/Documents/ERA'S ARENA/ERA_Avatar"])
