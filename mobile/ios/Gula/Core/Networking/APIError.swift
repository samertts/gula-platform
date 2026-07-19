import Foundation

enum APIError: Error, LocalizedError, Equatable {
    case authentication
    case tokenExpired
    case permissionDenied
    case notFound
    case conflict
    case validationFailed(errors: [String: [String]])
    case rateLimited(retryAfter: Int)
    case serverError(statusCode: Int)
    case networkError(underlying: Error)
    case timeout
    case offline
    case decodingError
    case unknown

    var errorDescription: String? {
        switch self {
        case .authentication: return "auth_error".localized
        case .tokenExpired: return "session_expired".localized
        case .permissionDenied: return "permission_denied".localized
        case .notFound: return "resource_not_found".localized
        case .conflict: return "resource_conflict".localized
        case .validationFailed: return "validation_error".localized
        case .rateLimited(let retryAfter): return String(format: "rate_limited".localized, retryAfter)
        case .serverError(let code): return String(format: "server_error_format".localized, code)
        case .networkError: return "network_error".localized
        case .timeout: return "request_timeout".localized
        case .offline: return "offline_message".localized
        case .decodingError: return "data_error".localized
        case .unknown: return "unknown_error".localized
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .authentication: return "auth_error_recovery".localized
        case .offline: return "offline_recovery".localized
        case .rateLimited(let retryAfter): return String(format: "rate_limited_recovery".localized, retryAfter)
        default: return "try_again".localized
        }
    }

    static func from(statusCode: Int, data: Data?) -> APIError {
        switch statusCode {
        case 401: return .authentication
        case 403: return .permissionDenied
        case 404: return .notFound
        case 409: return .conflict
        case 422:
            if let data = data,
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let errors = json["errors"] as? [String: [String]] {
                return .validationFailed(errors: errors)
            }
            return .validationFailed(errors: [:])
        case 429: return .rateLimited(retryAfter: 60)
        case 500...599: return .serverError(statusCode: statusCode)
        default: return .unknown
        }
    }

    static func == (lhs: APIError, rhs: APIError) -> Bool {
        switch (lhs, rhs) {
        case (.authentication, .authentication): return true
        case (.tokenExpired, .tokenExpired): return true
        case (.permissionDenied, .permissionDenied): return true
        case (.notFound, .notFound): return true
        case (.conflict, .conflict): return true
        case (.validationFailed, .validationFailed): return true
        case (.rateLimited, .rateLimited): return true
        case (.serverError, .serverError): return true
        case (.networkError, .networkError): return true
        case (.timeout, .timeout): return true
        case (.offline, .offline): return true
        case (.decodingError, .decodingError): return true
        case (.unknown, .unknown): return true
        default: return false
        }
    }
}
