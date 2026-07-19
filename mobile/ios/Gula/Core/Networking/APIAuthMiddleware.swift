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

            guard let url = URL(string: "\(APIClient.shared.baseURL)/auth/refresh") else {
                throw APIError.unknown
            }

            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            let body = ["refresh_token": refreshToken]
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.unknown
            }

            guard httpResponse.statusCode == 200 else {
                await AuthManager.shared.forceLogout()
                throw APIError.authentication
            }

            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            guard let newToken = json?["access_token"] as? String else {
                throw APIError.authentication
            }

            currentToken = newToken
            KeychainManager.shared.set(key: "access_token", value: newToken)

            if let newRefresh = json?["refresh_token"] as? String {
                KeychainManager.shared.set(key: "refresh_token", value: newRefresh)
            }

            return newToken
        }

        refreshTask = task
        return try await task.value
    }
}
