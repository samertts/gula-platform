import Foundation
import Combine

class AuthViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var isLoading = false
    @Published var error: APIError?
    @Published var errorMessage: String?
    @Published var showMFA = false
    @Published var mfaCode = ""
    @Published var showBiometricSetup = false
    @Published var showBiometricLogin = false
    @Published var isLoggedIn = false
    @Published var rememberMe = false
    @Published var validationErrors: [String: String] = [:]

    private let authManager = AuthManager.shared
    private var cancellables = Set<AnyCancellable>()

    var isFormValid: Bool {
        !email.isEmpty && !password.isEmpty && validationErrors.isEmpty
    }

    var canUseBiometric: Bool {
        BiometricAuth.isAvailable && KeychainManager.shared.get(key: "biometric_enabled") == "true"
    }

    func login() {
        guard isFormValid else {
            validateForm()
            return
        }

        isLoading = true
        error = nil
        errorMessage = nil

        Task {
            do {
                try await authManager.login(email: email, password: password)

                if rememberMe {
                    KeychainManager.shared.set(key: "saved_email", value: email)
                } else {
                    KeychainManager.shared.delete(key: "saved_email")
                }

                await MainActor.run {
                    self.isLoggedIn = true
                    self.isLoading = false
                    self.showBiometricSetup = BiometricAuth.isAvailable && !(KeychainManager.shared.get(key: "biometric_enabled") == "true")
                }
            } catch let apiError as APIError {
                await MainActor.run {
                    self.error = apiError
                    self.errorMessage = apiError.localizedDescription
                    self.isLoading = false
                    if case .authentication = apiError {
                        self.showMFA = true
                    }
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }

    func loginWithMFA() {
        guard !mfaCode.isEmpty else { return }

        isLoading = true
        Task {
            do {
                try await authManager.loginWithMFA(code: mfaCode)
                await MainActor.run {
                    self.isLoggedIn = true
                    self.showMFA = false
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }

    func loginWithBiometric() {
        isLoading = true
        Task {
            do {
                try await authManager.loginWithBiometric()
                await MainActor.run {
                    self.isLoggedIn = true
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }

    func logout() {
        authManager.logout()
        isLoggedIn = false
        email = ""
        password = ""
    }

    func enableBiometric() {
        authManager.enableBiometric(email: email, password: password)
        showBiometricSetup = false
    }

    func skipBiometric() {
        showBiometricSetup = false
    }

    func checkForSavedCredentials() {
        if let savedEmail = KeychainManager.shared.get(key: "saved_email") {
            email = savedEmail
            rememberMe = true
        }
    }

    private func validateForm() {
        validationErrors = [:]

        if email.isEmpty {
            validationErrors["email"] = "field_required".localized
        } else if !email.contains("@") {
            validationErrors["email"] = "invalid_email".localized
        }

        if password.isEmpty {
            validationErrors["password"] = "field_required".localized
        } else if password.count < 6 {
            validationErrors["password"] = "password_min_length".localized
        }
    }
}
