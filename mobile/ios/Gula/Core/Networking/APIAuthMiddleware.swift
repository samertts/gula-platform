import Foundation
import Combine

actor APIAuthMiddleware {
    static let shared = APIAuthMiddleware()

    private var currentToken: String?
    private var refreshTask: Task<String, Error>?

    private init() {}

    func getValidToken() async throws -> String {
        if let token = currentToken, !isTokenExpired(token) {
            return token
        }

        if let refreshToken = KeychainManager.shared.get(key: "refresh_token") {
            return try await refreshAccessToken(refreshToken: refreshToken)
        }

        throw APIError.authentication
    }

    func setToken(_ token: String) {
        currentToken = token
    }

    func clearToken() {
        currentToken = nil
        refreshTask = nil
    }

    private func isTokenExpired(_ token: String) -> Bool {
        let parts = token.split(separator: ".")
        guard parts.count == 3 else { return true }
        var base64 = String(parts[1])
        base64 = base64.replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        let paddedLength = base64.count + (4 - base64.count % 4) % 4
        base64 = base64.padding(toLength: paddedLength, withPad: "=", startingAt: 0)
        guard let data = Data(base64Encoded: base64),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let exp = json["exp"] as? TimeInterval else { return true }
        return Date().timeIntervalSince1970 > exp - 30
    }

    private func refreshAccessToken(refreshToken: String) async throws -> String {
        if let task = refreshTask {
            return try await task.value
        }

        let task = Task<String, Error> {
            defer { refreshTask = nil }
            do {
                // APIClient owns the pinned URLSession; never use the shared system
                // session for an authenticated or token-refresh request.
                let newToken = try await APIClient.shared.refreshTokenForMiddleware(refreshToken)
                currentToken = newToken
                return newToken
            } catch {
                await AuthManager.shared.forceLogout()
                throw error
            }
        }

        refreshTask = task
        return try await task.value
    }
}
