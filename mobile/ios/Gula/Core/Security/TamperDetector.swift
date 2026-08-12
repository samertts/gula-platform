import Foundation
import CommonCrypto
import UIKit

class TamperDetector {
    static let shared = TamperDetector()

    private let expectedBundleIdentifier = "com.gula.app"
    private let expectedSigningCertificateSubject = "GULA Platform"
    private let integrityCheckInterval: TimeInterval = 60

    private var isCompromised = false
    private var lastCheckTime: Date?

    private init() {}

    func performIntegrityCheck() -> IntegrityReport {
        let report = IntegrityReport(
            bundleIdentifierValid: checkBundleIdentifier(),
            signatureValid: checkSignature(),
            resourcesValid: checkResourcesIntegrity(),
            debuggerDetected: isDebuggerAttached(),
            isSimulator: isRunningInSimulator(),
            timestamp: Date()
        )

        if !report.isValid {
            isCompromised = true
            AnalyticsManager.shared.trackEvent("integrity_violation", parameters: report.dictionary)
        }

        lastCheckTime = Date()
        return report
    }

    func schedulePeriodicChecks() {
        Timer.scheduledTimer(withTimeInterval: integrityCheckInterval, repeats: true) { [weak self] _ in
            _ = self?.performIntegrityCheck()
        }
    }

    var appIsCompromised: Bool {
        isCompromised
    }

    private func checkBundleIdentifier() -> Bool {
        Bundle.main.bundleIdentifier == expectedBundleIdentifier
    }

    private func checkSignature() -> Bool {
        guard let executablePath = Bundle.main.executablePath else { return false }
        var fileStat = stat()
        guard stat(executablePath, &fileStat) == 0 else { return false }

        let fileHandle = FileHandle(forReadingAtPath: executablePath)
        defer { fileHandle?.closeFile() }
        guard let handle = fileHandle else { return false }

        let data = handle.readDataToEndOfFile()
        var hash = Data(count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes { buffer in
            hash.withUnsafeMutableBytes { hashBuffer in
                CC_SHA256(buffer.baseAddress, CC_LONG(data.count), hashBuffer.bindMemory(to: UInt8.self).baseAddress)
            }
        }

        let savedHash = UserDefaults.standard.data(forKey: "app_executable_hash")
        if savedHash == nil {
            UserDefaults.standard.set(hash, forKey: "app_executable_hash")
            return true
        }
        return hash == savedHash
    }

    private func checkResourcesIntegrity() -> Bool {
        let criticalResources = [
            "Info.plist",
            "GulaApp.swift"
        ]

        for resource in criticalResources {
            let path = Bundle.main.bundlePath + "/" + resource
            guard FileManager.default.fileExists(atPath: path) else {
                return false
            }
            let attributes = try? FileManager.default.attributesOfItem(atPath: path)
            guard let fileSize = attributes?[.size] as? Int64, fileSize > 0 else {
                return false
            }
        }
        return true
    }

    private func isDebuggerAttached() -> Bool {
        var info = kinfo_proc()
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
        var size = MemoryLayout<kinfo_proc>.stride
        let result = sysctl(&mib, u_int(mib.count), &info, &size, nil, 0)

        if result != 0 { return false }
        return (info.kp_proc.p_flag & P_TRACED) != 0
    }

    private func isRunningInSimulator() -> Bool {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }

    func checkForReverseEngineeringTools() -> [String] {
        var found: [String] = []
        let blacklist = [
            "frida", "cycript", "lldb", "gdb",
            "SSL Kill Switch 2", "Burp Suite",
            "Freedom", "Substrate"
        ]
        let processList = ProcessInfo.processInfo.arguments.joined(separator: " ")
        for tool in blacklist {
            if processList.lowercased().contains(tool.lowercased()) {
                found.append(tool)
            }
        }
        return found
    }

    func generateAppHash() -> String? {
        guard let executablePath = Bundle.main.executablePath,
              let data = FileManager.default.contents(atPath: executablePath) else {
            return nil
        }
        var hash = Data(count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes { buffer in
            hash.withUnsafeMutableBytes { hashBuffer in
                CC_SHA256(buffer.baseAddress, CC_LONG(data.count), hashBuffer.bindMemory(to: UInt8.self).baseAddress)
            }
        }
        return hash.map { String(format: "%02hhx", $0) }.joined()
    }
}

struct IntegrityReport {
    let bundleIdentifierValid: Bool
    let signatureValid: Bool
    let resourcesValid: Bool
    let debuggerDetected: Bool
    let isSimulator: Bool
    let timestamp: Date

    var isValid: Bool {
        bundleIdentifierValid && signatureValid && resourcesValid && !debuggerDetected && !isSimulator
    }

    var dictionary: [String: Any] {
        [
            "bundle_id_valid": bundleIdentifierValid,
            "signature_valid": signatureValid,
            "resources_valid": resourcesValid,
            "debugger_detected": debuggerDetected,
            "is_simulator": isSimulator,
            "is_valid": isValid,
            "timestamp": ISO8601DateFormatter().string(from: timestamp)
        ]
    }
}
