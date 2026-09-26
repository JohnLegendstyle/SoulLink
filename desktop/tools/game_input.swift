import AppKit
import CoreGraphics
import Foundation

// Development-only helper: explicit key/click events to the active test emulator.
guard let app = NSRunningApplication.runningApplications(withBundleIdentifier: "net.kuribo64.melonDS").first
    ?? NSWorkspace.shared.runningApplications.first(where: { $0.localizedName == "melonDS" }) else { exit(1) }
app.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
usleep(300_000)
for action in CommandLine.arguments.dropFirst() {
    let parts = action.split(separator: ":").map(String.init)
    if parts[0] == "wait", let seconds = Double(parts[1]) {
        Thread.sleep(forTimeInterval: seconds)
    } else if parts[0] == "mash", let key = UInt16(parts[1]), let count = Int(parts[2]) {
        for _ in 0..<count {
            let down = CGEvent(keyboardEventSource: nil, virtualKey: key, keyDown: true)!
            down.flags = []; down.postToPid(app.processIdentifier)
            usleep(120_000)
            let up = CGEvent(keyboardEventSource:nil, virtualKey:key, keyDown:false)!
            up.flags = []; up.postToPid(app.processIdentifier)
            usleep(180_000)
        }
    } else if parts[0] == "key", let key = UInt16(parts[1]) {
        let seconds = parts.count > 2 ? Double(parts[2])! : 0.15
        let down = CGEvent(keyboardEventSource: CGEventSource(stateID: .combinedSessionState), virtualKey: key, keyDown: true)!
        down.flags = []
        down.postToPid(app.processIdentifier)
        Thread.sleep(forTimeInterval: seconds)
        let up = CGEvent(keyboardEventSource: CGEventSource(stateID: .combinedSessionState), virtualKey: key, keyDown: false)!
        up.flags = []
        up.postToPid(app.processIdentifier)
        Thread.sleep(forTimeInterval: 0.15)
    } else if parts[0] == "click", let x = Double(parts[1]), let y = Double(parts[2]) {
        let p = CGPoint(x:x, y:y)
        CGEvent(mouseEventSource:nil, mouseType:.leftMouseDown, mouseCursorPosition:p, mouseButton:.left)?.post(tap:.cghidEventTap)
        usleep(100_000)
        CGEvent(mouseEventSource:nil, mouseType:.leftMouseUp, mouseCursorPosition:p, mouseButton:.left)?.post(tap:.cghidEventTap)
        usleep(350_000)
    }
}
