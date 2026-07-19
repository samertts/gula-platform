import Cocoa
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    let windowFrame = NSRect(x: 0, y: 0, width: 1280, height: 800)
    self.contentViewController = flutterViewController
    self.setFrame(windowFrame, display: true)
    self.title = "GULA Platform"
    self.minSize = NSSize(width: 800, height: 600)
    self.maxSize = NSSize(width: 2560, height: 1600)
    self.styleMask.insert(.fullSizeContentView)
    self.titlebarAppearsTransparent = true
    self.isMovableByWindowBackground = true

    if #available(macOS 11.0, *) {
      self.toolbarStyle = .unified
    }

    RegisterGeneratedPlugins(registry: flutterViewController)

    super.awakeFromNib()
  }

  override func close() {
    NSApp.hide(nil)
  }
}
