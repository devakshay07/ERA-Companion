import Cocoa
import WebKit

class DraggableWindow: NSWindow {
    override var canBecomeKey: Bool { return false }
    override var canBecomeMain: Bool { return false }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: DraggableWindow!
    var defaultRect: NSRect!
    var evadeRect: NSRect!
    var isEvading = false
    
    func applicationDidFinishLaunching(_ aNotification: Notification) {
        let screenRect = NSScreen.main?.visibleFrame ?? NSRect(x: 0, y: 0, width: 800, height: 600)
        
        let width: CGFloat = 700
        let height: CGFloat = screenRect.height // Force window to span the entire height of the display
        
        defaultRect = NSRect(x: screenRect.maxX - width, y: screenRect.minY, width: width, height: height)
        evadeRect = NSRect(x: screenRect.minX, y: screenRect.minY, width: width, height: height)
        
        // Strict Singleton Lock
        let lockFilePath = NSTemporaryDirectory() + "era_avatar_swift.lock"
        let lockFileDescriptor = open(lockFilePath, O_RDWR | O_CREAT, 0o666)
        if lockFileDescriptor < 0 || flock(lockFileDescriptor, LOCK_EX | LOCK_NB) != 0 {
            print("Strict lock violation: Another instance of ERA Avatar is already running. Assassinating self.")
            NSApplication.shared.terminate(nil)
        }
        
        window = DraggableWindow(contentRect: defaultRect,
                          styleMask: [.borderless],
                          backing: .buffered,
                          defer: false)
        
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary, .ignoresCycle]
        window.level = .floating
        window.backgroundColor = .clear
        window.isOpaque = false
        window.hasShadow = false
        window.ignoresMouseEvents = false 
        
        let webConfiguration = WKWebViewConfiguration()
        webConfiguration.preferences.setValue(true, forKey: "developerExtrasEnabled")
        
        let webView = WKWebView(frame: window.contentView!.bounds, configuration: webConfiguration)
        webView.autoresizingMask = [.width, .height]
        webView.setValue(false, forKey: "drawsBackground")
        
        let css = "body { pointer-events: none !important; } #audio-controls { display: none !important; }"
        let script = WKUserScript(source: "var style = document.createElement('style'); style.innerHTML = '\(css)'; document.head.appendChild(style);", injectionTime: .atDocumentEnd, forMainFrameOnly: true)
        webView.configuration.userContentController.addUserScript(script)
        
        let randomNum = Int.random(in: 1...100000)
        let url = URL(string: "http://localhost:8000/avatar.html?v=\(randomNum)")!
        webView.load(URLRequest(url: url))
        
        window.contentView?.addSubview(webView)
        window.makeKeyAndOrderFront(nil)
        
        // Jitter-free Teleport Logic - CORRECTED
        Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            let mouseLoc = NSEvent.mouseLocation
            let midX = screenRect.minX + (screenRect.width / 2)
            
            if mouseLoc.x > midX { 
                // Mouse is on the right side. She must evade to the left.
                if !self.isEvading {
                    self.isEvading = true
                    NSAnimationContext.runAnimationGroup({ context in
                        context.duration = 0.3
                        context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
                        self.window.animator().setFrame(self.evadeRect, display: true)
                    })
                }
            } else {
                // Mouse is on the left side (or middle). She must return to the right.
                if self.isEvading {
                    self.isEvading = false
                    NSAnimationContext.runAnimationGroup({ context in
                        context.duration = 0.3
                        context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
                        self.window.animator().setFrame(self.defaultRect, display: true)
                    })
                }
            }
        }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
