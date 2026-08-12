import Foundation
import Combine
import UIKit

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private let monitor = NWPathMonitor()

    private var baseURL: String {
        UserDefaults.standard.string(forKey: "api_base_url") ?? "https://api.gula-platform.org/api/v1"
    }

    private var accessToken: String? {
        KeychainManager.shared.get(key: "access_token")
    }

    private var refreshToken: String? {
        KeychainManager.shared.get(key: "refresh_token")
    }

    private var isRefreshing = false
    private var pendingRequests: [(Result<String, APIError>) -> Void] = []

    private init() {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        config.waitsForConnectivity = true
        config.httpAdditionalHeaders = [
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Client-Platform": "ios",
            "X-Client-Version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
        ]

        let delegate = CertificatePinner()
        session = URLSession(configuration: config, delegate: delegate, delegateQueue: nil)

        decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601

        encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
    }

    func request<T: Decodable>(_ endpoint: APIEndpoint, body: Encodable? = nil) async throws -> T {
        return try await performRequest(endpoint, body: body)
    }

    func requestVoid(_ endpoint: APIEndpoint, body: Encodable? = nil) async throws {
        let _: EmptyResponse = try await performRequest(endpoint, body: body)
    }

    func requestData(_ endpoint: APIEndpoint) async throws -> Data {
        var urlRequest = try buildRequest(endpoint)
        try await injectAuth(&urlRequest)
        return try await performDataRequest(urlRequest)
    }

    func upload<T: Decodable>(_ endpoint: APIEndpoint, data: Data, mimeType: String, fileName: String) async throws -> T {
        var request = try buildRequest(endpoint)
        try await injectAuth(&request)

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (responseData, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.unknown
        }
        try validateResponse(httpResponse, data: responseData)
        return try decoder.decode(T.self, from: responseData)
    }

    func download(url: String) async throws -> Data {
        guard let url = URL(string: url) else { throw APIError.unknown }
        var request = URLRequest(url: url)
        try await injectAuth(&request)
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIError.serverError(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 500)
        }
        return data
    }

    private func performRequest<T: Decodable>(_ endpoint: APIEndpoint, body: Encodable?) async throws -> T {
        var urlRequest = try buildRequest(endpoint)

        if let body = body {
            urlRequest.httpBody = try encoder.encode(AnyEncodable(body))
        }

        try await injectAuth(&urlRequest)
        let (data, _) = try await performRequestWithRetry(urlRequest)
        return try decoder.decode(T.self, from: data)
    }

    private func buildRequest(_ endpoint: APIEndpoint) throws -> URLRequest {
        guard let url = URL(string: baseURL + endpoint.path) else {
            throw APIError.unknown
        }
        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return request
    }

    private func injectAuth(_ request: inout URLRequest) async throws {
        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }

    private func performRequestWithRetry(_ request: URLRequest, retries: Int = 3) async throws -> (Data, HTTPURLResponse) {
        var lastError: Error?

        for attempt in 0..<retries {
            do {
                let (data, response) = try await session.data(for: request)
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw APIError.unknown
                }

                if httpResponse.statusCode == 401, let refreshToken = refreshToken {
                    let newToken = try await refreshAccessToken(refreshToken: refreshToken)
                    var newRequest = request
                    newRequest.setValue("Bearer \(newToken)", forHTTPHeaderField: "Authorization")
                    let (retryData, retryResponse) = try await session.data(for: newRequest)
                    guard let retryHttpResponse = retryResponse as? HTTPURLResponse else {
                        throw APIError.unknown
                    }
                    try validateResponse(retryHttpResponse, data: retryData)
                    return (retryData, retryHttpResponse)
                }

                try validateResponse(httpResponse, data: data)
                return (data, httpResponse)
            } catch let error as APIError {
                lastError = error
                if case .authentication = error { throw error }
                if attempt < retries - 1 {
                    let delay = Double(pow(2.0, Double(attempt))) * 0.5
                    try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                }
            } catch {
                lastError = error
                if attempt < retries - 1 {
                    let delay = Double(pow(2.0, Double(attempt))) * 0.5
                    try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                }
            }
        }

        throw lastError ?? APIError.unknown
    }

    private func performDataRequest(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.unknown
        }
        try validateResponse(httpResponse, data: data)
        return data
    }

    private func validateResponse(_ response: HTTPURLResponse, data: Data) throws {
        switch response.statusCode {
        case 200...299: return
        case 401:
            NotificationCenter.default.post(name: .sessionExpired, object: nil)
            throw APIError.authentication
        case 403: throw APIError.permissionDenied
        case 404: throw APIError.notFound
        case 409: throw APIError.conflict
        case 422: throw APIError.from(statusCode: response.statusCode, data: data)
        case 429: throw APIError.rateLimited(retryAfter: 60)
        default: throw APIError.serverError(statusCode: response.statusCode)
        }
    }

    private func refreshAccessToken(refreshToken: String) async throws -> String {
        if isRefreshing {
            return try await withCheckedThrowingContinuation { continuation in
                pendingRequests.append { result in
                    switch result {
                    case .success(let token): continuation.resume(returning: token)
                    case .failure(let error): continuation.resume(throwing: error)
                    }
                }
            }
        }

        isRefreshing = true
        defer {
            isRefreshing = false
            let requests = pendingRequests
            pendingRequests.removeAll()
            for request in requests {
                request(.failure(APIError.authentication))
            }
        }

        guard let url = URL(string: baseURL + "/auth/refresh") else {
            throw APIError.unknown
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body = ["refresh_token": refreshToken]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            await AuthManager.shared.forceLogout()
            throw APIError.authentication
        }

        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let newToken = json?["access_token"] as? String else {
            throw APIError.authentication
        }

        KeychainManager.shared.set(key: "access_token", value: newToken)
        let requests = pendingRequests
        pendingRequests.removeAll()
        for req in requests {
            req(.success(newToken))
        }

        return newToken
    }

    func setTokens(access: String, refresh: String) {
        KeychainManager.shared.set(key: "access_token", value: access)
        KeychainManager.shared.set(key: "refresh_token", value: refresh)
    }

    func clearTokens() {
        KeychainManager.shared.delete(key: "access_token")
        KeychainManager.shared.delete(key: "refresh_token")
    }

    func registerDeviceToken(token: String, platform: String) async throws {
        let _: EmptyResponse = try await performRequest(
            APIEndpoint.registerDevice(token: token, platform: platform),
            body: DeviceTokenRequest(deviceToken: token, platform: platform)
        )
    }
}

extension Notification.Name {
    static let sessionExpired = Notification.Name("sessionExpired")
}

struct EmptyResponse: Decodable {}

struct AnyEncodable: Encodable {
    let value: Encodable
    init(_ value: Encodable) { self.value = value }
    func encode(to encoder: Encoder) throws { try value.encode(to: encoder) }
}

struct DeviceTokenRequest: Encodable {
    let deviceToken: String
    let platform: String
}
