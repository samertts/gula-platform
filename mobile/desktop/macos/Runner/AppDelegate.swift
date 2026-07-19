import Cocoa
import FlutterMacOS

@NSApplicationMain
class AppDelegate: FlutterAppDelegate {
  private var methodChannel: FlutterMethodChannel?

  override func applicationSupportsSecureRestorableState(_ application: NSApplication) -> Bool {
    return true
  }

  override func applicationDidFinishLaunching(_ notification: Notification) {
    let controller = self.mainFlutterWindow?.contentViewController as! FlutterViewController
    methodChannel = FlutterMethodChannel(
      name: "com.gula.platform/desktop",
      binaryMessenger: controller.engine.binaryMessenger
    )

    methodChannel?.setMethodCallHandler { [weak self] (call, result) in
      switch call.method {
      case "getPlatformVersion":
        result(ProcessInfo.processInfo.operatingSystemVersionString)
      case "getDeviceName":
        result(Host.current().localizedName ?? "Mac")
      case "minimizeToTray":
        NSApp.hide(nil)
        result(true)
      case "restoreFromTray":
        NSApp.unhide(nil)
        self?.mainFlutterWindow?.makeKeyAndOrderFront(nil)
        result(true)
      case "setBadgeLabel":
        if let args = call.arguments as? [String: Any],
           let label = args["label"] as? String {
          NSApp.dockTile.badgeLabel = label.isEmpty ? nil : label
          result(true)
        } else {
          result(FlutterError(code: "INVALID_ARGS", message: nil, details: nil))
        }
      default:
        result(FlutterMethodNotImplemented)
      }
    }
  }

  override func applicationShouldHandleReopen(
    _ sender: NSApplication,
    hasVisibleWindows flag: Bool
  ) -> Bool {
    if !flag {
      mainFlutterWindow?.makeKeyAndOrderFront(nil)
    }
    return true
  }

  override func application(_ application: NSApplication, open urls: [URL]) {
    for url in urls {
      if url.scheme == "gula" {
        NotificationCenter.default.post(
          name: Notification.Name("GulaDeepLink"),
          object: url
        )
      }
    }
  }
}
