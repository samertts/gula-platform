import Foundation
import Combine

class AuthManager: ObservableObject {
    static let shared = AuthManager()

    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var error: APIError?
    @Published var requiresMFA = false
    @Published var mfaSession: String?
    @Published var biometricEnabled = false

    private var cancellables = Set<AnyCancellable>()

    private init() {
        checkExistingSession()
        biometricEnabled = KeychainManager.shared.get(key: "biometric_enabled") == "true"
    }

    var isLoggedIn: Bool {
        isAuthenticated && currentUser != nil
    }

    var canUseBiometric: Bool {
        biometricEnabled && BiometricAuth.isAvailable
    }

    func login(email: String, password: String) async throws {
        await MainActor.run { isLoading = true; error = nil }

        do {
            let response: LoginResponse = try await APIClient.shared.request(
                .login,
                body: ["email": email, "password": password]
            )

            await MainActor.run {
                APIClient.shared.setTokens(access: response.accessToken, refresh: response.refreshToken)

                let user = User(
                    id: response.user.id,
                    email: response.user.email,
                    name: response.user.name,
                    role: UserRole(rawValue: response.user.role) ?? .staff,
                    labId: response.user.labId
                )
                self.currentUser = user
                self.isAuthenticated = true
                self.isLoading = false
                saveUserSession(user: user)
            }
        } catch {
            await MainActor.run {
                isLoading = false
                if let apiError = error as? APIError {
                    self.error = apiError
                } else {
                    self.error = .networkError(underlying: error)
                }
            }
            throw error
        }
    }

    func loginWithMFA(code: String) async throws {
        guard let session = mfaSession else { throw APIError.authentication }
        await MainActor.run { isLoading = true; error = nil }

        do {
            let response: LoginResponse = try await APIClient.shared.request(
                .login,
                body: ["mfa_code": code, "mfa_session": session]
            )

            await MainActor.run {
                APIClient.shared.setTokens(access: response.accessToken, refresh: response.refreshToken)
                let user = User(
                    id: response.user.id,
                    email: response.user.email,
                    name: response.user.name,
                    role: UserRole(rawValue: response.user.role) ?? .staff,
                    labId: response.user.labId
                )
                self.currentUser = user
                self.isAuthenticated = true
                self.requiresMFA = false
                self.mfaSession = nil
                self.isLoading = false
                saveUserSession(user: user)
            }
        } catch {
            await MainActor.run { isLoading = false }
            throw error
        }
    }

    func loginWithBiometric() async throws {
        do {
            let authenticated = try await BiometricAuth.authenticate()
            guard authenticated else { throw BiometricAuth.BiometricError.failed }

            guard let email = KeychainManager.shared.get(key: "biometric_email"),
                  let password = KeychainManager.shared.get(key: "biometric_password") else {
                throw BiometricAuth.BiometricError.notAvailable
            }

            try await login(email: email, password: password)
        } catch {
            self.error = .authentication
            throw error
        }
    }

    func logout() async {
        let token = KeychainManager.shared.get(key: "access_token")
        if let token {
            try? await APIClient.shared.serverLogout(accessToken: token)
        }
        await clearLocalSession()
    }

    func forceLogout() async {
        await logout()
        await MainActor.run {
            NotificationCenter.default.post(name: .sessionExpired, object: nil)
        }
    }

    private func clearLocalSession() async {
        await APIClient.shared.clearTokens()
        await MainActor.run {
            UserDefaults.standard.removeObject(forKey: "current_user_id")
            UserDefaults.standard.removeObject(forKey: "current_user_role")
            UserDefaults.standard.removeObject(forKey: "current_user_name")
            UserDefaults.standard.removeObject(forKey: "current_user_lab_id")
            UserDefaults.standard.synchronize()

            currentUser = nil
            isAuthenticated = false
            requiresMFA = false
            mfaSession = nil
        }
    }

    func enableBiometric(email: String, password: String) {
        KeychainManager.shared.set(key: "biometric_email", value: email)
        KeychainManager.shared.set(key: "biometric_password", value: password)
        KeychainManager.shared.set(key: "biometric_enabled", value: "true")
        biometricEnabled = true
    }

    func disableBiometric() {
        KeychainManager.shared.delete(key: "biometric_email")
        KeychainManager.shared.delete(key: "biometric_password")
        KeychainManager.shared.set(key: "biometric_enabled", value: "false")
        biometricEnabled = false
    }

    private func checkExistingSession() {
        guard let userId = UserDefaults.standard.object(forKey: "current_user_id") as? Int,
              let role = UserDefaults.standard.string(forKey: "current_user_role"),
              let name = UserDefaults.standard.string(forKey: "current_user_name"),
              let email = KeychainManager.shared.get(key: "session_email") else {
            return
        }

        guard KeychainManager.shared.get(key: "access_token") != nil else {
            return
        }

        currentUser = User(
            id: userId,
            email: email,
            name: name,
            role: UserRole(rawValue: role) ?? .staff,
            labId: UserDefaults.standard.object(forKey: "current_user_lab_id") as? Int
        )
        isAuthenticated = true
    }

    private func saveUserSession(user: User) {
        UserDefaults.standard.set(user.id, forKey: "current_user_id")
        UserDefaults.standard.set(user.role.rawValue, forKey: "current_user_role")
        UserDefaults.standard.set(user.name, forKey: "current_user_name")
        if let labId = user.labId {
            UserDefaults.standard.set(labId, forKey: "current_user_lab_id")
        }
        KeychainManager.shared.set(key: "session_email", value: user.email)
        UserDefaults.standard.synchronize()
    }
}

struct User: Identifiable, Equatable {
    let id: Int
    let email: String
    let name: String
    let role: UserRole
    let labId: Int?
}

enum UserRole: String, Codable, CaseIterable {
    case labAdmin = "lab_admin"
    case technician = "technician"
    case doctor = "doctor"
    case staff = "staff"
    case receptionist = "receptionist"
    case masterAdmin = "master_admin"
    case ministryAdmin = "ministry_admin"
    case provinceAdmin = "province_admin"
    case patient = "patient"
    case citizen = "citizen"
    case monitoring = "monitoring"

    var displayName: String {
        switch self {
        case .labAdmin: return "role_lab_admin".localized
        case .technician: return "role_technician".localized
        case .doctor: return "role_doctor".localized
        case .staff: return "role_staff".localized
        case .receptionist: return "role_receptionist".localized
        case .masterAdmin: return "role_master_admin".localized
        case .ministryAdmin: return "role_ministry_admin".localized
        case .provinceAdmin: return "role_province_admin".localized
        case .patient: return "role_patient".localized
        case .citizen: return "role_citizen".localized
        case .monitoring: return "role_monitoring".localized
        }
    }
}

struct LoginResponse: Decodable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let expiresIn: Int
    let user: UserBrief

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
        case expiresIn = "expires_in"
        case user
    }
}

struct UserBrief: Decodable {
    let id: Int
    let email: String
    let name: String
    let role: String
    let labId: Int?

    enum CodingKeys: String, CodingKey {
        case id, email, name, role
        case labId = "lab_id"
    }
}
