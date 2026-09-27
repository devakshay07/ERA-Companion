import webview
import os
import threading
import http.server
import socketserver
import time
import json

import fcntl

lock_file_path = os.path.expanduser("~/.era_avatar.lock")
lock_file_fd = open(lock_file_path, 'w')
try:
    fcntl.lockf(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("Another instance of ERA Avatar is already running. Exiting.")
    sys.exit(0)


VOICE_DIR = os.path.expanduser("~/.gemini/antigravity/era_voice")
SPEAKING_FLAG = os.path.join(VOICE_DIR, ".era_speaking")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

# Run a quick local HTTP server and state bridge
def start_server_and_bridge():
    PORT = 8000
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    Handler = http.server.SimpleHTTPRequestHandler
    
    class QuietHandler(Handler):
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
    with open(STATE_FILE, 'w') as f:
        json.dump({"speaking": False, "emotion": "neutral"}, f)
        
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
                
            current_state = {"speaking": is_speaking, "emotion": current_emotion}
            if current_state != last_state:
                with open(STATE_FILE, 'w') as f:
                    json.dump(current_state, f)
                last_state = current_state
            time.sleep(0.05)
        except Exception:
            time.sleep(0.5)

if __name__ == '__main__':
    # Start server in background
    server_thread = threading.Thread(target=start_server_and_bridge, daemon=True)
    server_thread.start()

    # Calculate bottom-left coordinates
    try:
        import AppKit
        screen = AppKit.NSScreen.mainScreen().frame()
        screen_height = int(screen.size.height)
        y_pos = screen_height - 900 - 50 # 50px padding from bottom
    except Exception:
        y_pos = 200

    # Create transparent, frameless window (Larger frame for gestures)
    import random
    window = webview.create_window(
        'ERA Avatar',
        f'http://localhost:8000/avatar.html?v={random.randint(1, 100000)}',
        transparent=True,
        frameless=True,
        on_top=True,
        width=1000,
        height=900,
        x=20,
        y=y_pos
    )
    
    # Start the GUI loop
    webview.start(gui='cocoa')
