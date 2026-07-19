import Foundation
import Combine
import UIKit

class SessionManager: ObservableObject {
    static let shared = SessionManager()

    @Published var isSessionValid = true
    @Published var lastActivityDate: Date = Date()
    @Published var sessionTimeoutRemaining: TimeInterval = 0

    private let sessionTimeout: TimeInterval = 15 * 60
    private let gracePeriod: TimeInterval = 60
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    private var timer: Timer?
    private var cancellables = Set<AnyCancellable>()
    private var isBackgrounded = false

    private init() {
        startActivityMonitor()
        observeAppLifecycle()
    }

    func recordActivity() {
        lastActivityDate = Date()
        isSessionValid = true
        updateRemainingTime()
    }

    func startActivityMonitor() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            self?.checkSessionValidity()
        }
    }

    func stopActivityMonitor() {
        timer?.invalidate()
        timer = nil
    }

    private func checkSessionValidity() {
        let idleTime = Date().timeIntervalSince(lastActivityDate)

        if idleTime >= sessionTimeout {
            isSessionValid = false
            sessionTimeoutRemaining = 0
            NotificationCenter.default.post(name: .sessionDidExpire, object: nil)
        } else {
            isSessionValid = true
            sessionTimeoutRemaining = sessionTimeout - idleTime
        }
    }

    private func updateRemainingTime() {
        let idleTime = Date().timeIntervalSince(lastActivityDate)
        sessionTimeoutRemaining = max(0, sessionTimeout - idleTime)
    }

    private func observeAppLifecycle() {
        NotificationCenter.default.publisher(for: UIApplication.willResignActiveNotification)
            .sink { [weak self] _ in
                self?.handleAppBackgrounding()
            }
            .store(in: &cancellables)

        NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)
            .sink { [weak self] _ in
                self?.handleAppForegrounding()
            }
            .store(in: &cancellables)

        NotificationCenter.default.publisher(for: UIApplication.willTerminateNotification)
            .sink { [weak self] _ in
                self?.handleAppTermination()
            }
            .store(in: &cancellables)
    }

    private func handleAppBackgrounding() {
        isBackgrounded = true
        backgroundTask = UIApplication.shared.beginBackgroundTask { [weak self] in
            self?.endBackgroundTask()
        }
        recordActivity()
    }

    private func handleAppForegrounding() {
        isBackgrounded = false
        let backgroundDuration = Date().timeIntervalSince(lastActivityDate)
        endBackgroundTask()

        if backgroundDuration >= sessionTimeout {
            isSessionValid = false
            sessionTimeoutRemaining = 0
            if BiometricAuth.isAvailable {
                NotificationCenter.default.post(name: .requireBiometricAuth, object: nil)
            } else {
                NotificationCenter.default.post(name: .requirePasscodeAuth, object: nil)
            }
        } else {
            recordActivity()
        }
    }

    private func handleAppTermination() {
        stopActivityMonitor()
        endBackgroundTask()
    }

    private func endBackgroundTask() {
        if backgroundTask != .invalid {
            UIApplication.shared.endBackgroundTask(backgroundTask)
            backgroundTask = .invalid
        }
    }

    func extendSession() {
        lastActivityDate = Date()
        isSessionValid = true
        updateRemainingTime()
    }

    func invalidateSession() {
        isSessionValid = false
        sessionTimeoutRemaining = 0
        stopActivityMonitor()
    }
}

extension Notification.Name {
    static let sessionDidExpire = Notification.Name("sessionDidExpire")
    static let requireBiometricAuth = Notification.Name("requireBiometricAuth")
    static let requirePasscodeAuth = Notification.Name("requirePasscodeAuth")
}
