import Foundation
import LocalAuthentication

class BiometricAuth {
    enum BiometricType {
        case faceID
        case touchID
        case none
    }

    enum BiometricError: LocalizedError {
        case notAvailable
        case notEnrolled
        case lockout
        case cancelled
        case failed
        case unknown(String)

        var errorDescription: String? {
            switch self {
            case .notAvailable: return "biometric_not_available".localized
            case .notEnrolled: return "biometric_not_enrolled".localized
            case .lockout: return "biometric_lockout".localized
            case .cancelled: return "biometric_cancelled".localized
            case .failed: return "biometric_failed".localized
            case .unknown(let message): return message
            }
        }
    }

    static var biometryType: BiometricType {
        let context = LAContext()
        var error: NSError?

        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            return .none
        }

        switch context.biometryType {
        case .faceID: return .faceID
        case .touchID: return .touchID
        default: return .none
        }
    }

    static var isAvailable: Bool {
        let context = LAContext()
        var error: NSError?
        return context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error)
    }

    static func authenticate(reason: String = "authenticate_reason".localized) async throws -> Bool {
        let context = LAContext()
        context.interactionNotAllowed = false
        context.localizedFallbackTitle = "use_passcode".localized
        context.localizedCancelTitle = "cancel".localized

        var error: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            if let laError = error {
                throw mapLAError(laError)
            }
            throw BiometricError.notAvailable
        }

        return try await withCheckedThrowingContinuation { continuation in
            context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { success, error in
                DispatchQueue.main.async {
                    if success {
                        continuation.resume(returning: true)
                    } else if let laError = error as? LAError {
                        continuation.resume(throwing: mapLAError(laError as NSError))
                    } else {
                        continuation.resume(throwing: BiometricError.failed)
                    }
                }
            }
        }
    }

    private static func mapLAError(_ error: NSError) -> BiometricError {
        switch error.code {
        case LAError.biometryNotAvailable.rawValue: return .notAvailable
        case LAError.biometryNotEnrolled.rawValue: return .notEnrolled
        case LAError.biometryLockout.rawValue: return .lockout
        case LAError.userCancel.rawValue, LAError.appCancel.rawValue,
             LAError.systemCancel.rawValue: return .cancelled
        case LAError.authenticationFailed.rawValue: return .failed
        default: return .unknown(error.localizedDescription)
        }
    }

    static func canEvaluatePolicy() -> Bool {
        let context = LAContext()
        var error: NSError?
        return context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error)
    }
}
