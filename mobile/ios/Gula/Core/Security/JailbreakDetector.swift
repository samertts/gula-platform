import Foundation
import UIKit

class JailbreakDetector {
    static var isJailbroken: Bool {
        #if targetEnvironment(simulator)
        return false
        #else
        return checkCommonPaths() || checkSandboxViolation() || checkSymlinks() || checkFork()
        #endif
    }

    static var jailbreakRiskLevel: RiskLevel {
        let checks = [
            checkCommonPaths(),
            checkSandboxViolation(),
            checkSymlinks(),
            checkFork(),
            checkDYLD(),
            checkCydia()
        ]
        let positive = checks.filter { $0 }.count
        switch positive {
        case 0: return .none
        case 1: return .low
        case 2: return .medium
        default: return .high
        }
    }

    enum RiskLevel: Int {
        case none = 0
        case low = 1
        case medium = 2
        case high = 3

        var description: String {
            switch self {
            case .none: return "jailbreak_none".localized
            case .low: return "jailbreak_low".localized
            case .medium: return "jailbreak_medium".localized
            case .high: return "jailbreak_high".localized
            }
        }
    }

    private static let jailbreakPaths = [
        "/Applications/Cydia.app",
        "/Applications/FakeCarrier.app",
        "/Applications/Icy.app",
        "/Applications/IntelliScreen.app",
        "/Applications/MxTube.app",
        "/Applications/RockApp.app",
        "/Applications/SBSettings.app",
        "/Applications/WinterBoard.app",
        "/Applications/blackra1n.app",
        "/Library/MobileSubstrate/MobileSubstrate.dylib",
        "/Library/MobileSubstrate/DynamicLibraries",
        "/Library/MobileSubstrate/DynamicLibraries/Veency.plist",
        "/Library/MobileSubstrate/MobileSubstrate.dylib",
        "/System/Library/LaunchDaemons/com.ikey.bbot.plist",
        "/System/Library/LaunchDaemons/com.saurik.Cydia.Startup.plist",
        "/bin/bash",
        "/bin/sh",
        "/etc/apt",
        "/etc/ssh/sshd_config",
        "/private/var/lib/apt",
        "/private/var/lib/cydia",
        "/private/var/mobile/Library/SBSettings/Themes",
        "/private/var/stash",
        "/private/var/tmp/cydia.log",
        "/usr/bin/sshd",
        "/usr/libexec/sftp-server",
        "/usr/libexec/ssh-keysign",
        "/usr/sbin/sshd",
        "/var/cache/apt",
        "/var/lib/apt",
        "/var/lib/cydia",
        "/var/log/syslog",
        "/var/tmp/cydia.log"
    ]

    private static func checkCommonPaths() -> Bool {
        for path in jailbreakPaths {
            if FileManager.default.fileExists(atPath: path) {
                return true
            }
        }
        return false
    }

    private static func checkSandboxViolation() -> Bool {
        do {
            try "test".write(toFile: "/private/jailbreak-test.txt", atomically: true, encoding: .utf8)
            try FileManager.default.removeItem(atPath: "/private/jailbreak-test.txt")
            return true
        } catch {
            return false
        }
    }

    private static func checkSymlinks() -> Bool {
        let paths = ["/Applications", "/Library/Ringtones", "/Library/Wallpaper", "/usr/libexec", "/usr/share"]
        for path in paths {
            if let attributes = try? FileManager.default.attributesOfItem(atPath: path),
               let fileType = attributes[.type] as? FileAttributeType,
               fileType == .typeSymbolicLink {
                let linkPath = try? FileManager.default.destinationOfSymbolicLink(atPath: path)
                if linkPath?.hasPrefix("/private/var/mobile/") == true {
                    return true
                }
            }
        }
        return false
    }

    private static func checkFork() -> Bool {
        let pointer = UnsafeMutableRawPointer(bitPattern: -2)
        let forkPtr = dlsym(pointer, "fork")
        typealias ForkType = @convention(c) () -> pid_t
        if let fork = unsafeBitCast(forkPtr, to: ForkType.self) as (() -> pid_t)? {
            let result = fork()
            if result >= 0 {
                kill(result, SIGTERM)
                return true
            }
        }
        return false
    }

    private static func checkDYLD() -> Bool {
        let env = environ
        var i = 0
        while env[i] != nil {
            if let varStr = String(validatingUTF8: env[i]) {
                if varStr.contains("DYLD_INSERT_LIBRARIES") {
                    return true
                }
            }
            i += 1
        }
        return false
    }

    private static func checkCydia() -> Bool {
        if let url = URL(string: "cydia://package/com.gula.app"),
           UIApplication.shared.canOpenURL(url) {
            return true
        }
        return false
    }
}
