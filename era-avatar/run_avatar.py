import webview
import os
import threading
import http.server
import socketserver
import time
import json

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
    window = webview.create_window(
        'ERA Avatar',
        'http://localhost:8000/avatar.html',
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
