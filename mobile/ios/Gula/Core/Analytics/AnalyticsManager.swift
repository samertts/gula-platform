import Foundation
import UIKit

class AnalyticsManager {
    static let shared = AnalyticsManager()

    private var isEnabled = true
    private var sessionId: String
    private var eventQueue: [AnalyticsEvent] = []
    private let queue = DispatchQueue(label: "com.gula.analytics", qos: .background)

    private init() {
        sessionId = UUID().uuidString
        isEnabled = !UserDefaults.standard.bool(forKey: "analytics_opt_out")
    }

    func setOptOut(_ optOut: Bool) {
        isEnabled = !optOut
        UserDefaults.standard.set(optOut, forKey: "analytics_opt_out")
    }

    func trackScreen(_ screenName: String, screenClass: String? = nil) {
        guard isEnabled else { return }
        let event = AnalyticsEvent(
            name: "screen_view",
            parameters: [
                "screen_name": screenName,
                "screen_class": screenClass ?? screenName,
                "session_id": sessionId
            ]
        )
        enqueue(event)
    }

    func trackEvent(_ name: String, parameters: [String: Any]? = nil) {
        guard isEnabled else { return }
        var params = parameters ?? [:]
        params["session_id"] = sessionId
        let event = AnalyticsEvent(name: name, parameters: params)
        enqueue(event)
    }

    func trackError(_ error: Error, context: String? = nil) {
        guard isEnabled else { return }
        var params: [String: Any] = [
            "error": error.localizedDescription,
            "error_domain": (error as NSError).domain,
            "error_code": (error as NSError).code
        ]
        if let context = context {
            params["context"] = context
        }
        let event = AnalyticsEvent(name: "error", parameters: params)
        enqueue(event)
    }

    func trackPerformance(metric: String, durationMs: Double) {
        guard isEnabled else { return }
        let event = AnalyticsEvent(
            name: "performance",
            parameters: [
                "metric": metric,
                "duration_ms": durationMs,
                "session_id": sessionId
            ]
        )
        enqueue(event)
    }

    func trackUserAction(_ action: String, target: String? = nil) {
        guard isEnabled else { return }
        var params: [String: Any] = ["action": action]
        if let target = target {
            params["target"] = target
        }
        params["session_id"] = sessionId
        let event = AnalyticsEvent(name: "user_action", parameters: params)
        enqueue(event)
    }

    func logNetworkRequest(url: String, method: String, statusCode: Int, durationMs: Double) {
        guard isEnabled else { return }
        let event = AnalyticsEvent(
            name: "network_request",
            parameters: [
                "url": url,
                "method": method,
                "status_code": statusCode,
                "duration_ms": durationMs,
                "session_id": sessionId
            ]
        )
        enqueue(event)
    }

    func logSyncEvent(entityType: String, operation: String, success: Bool, durationMs: Double) {
        guard isEnabled else { return }
        let event = AnalyticsEvent(
            name: "sync_operation",
            parameters: [
                "entity_type": entityType,
                "operation": operation,
                "success": success,
                "duration_ms": durationMs,
                "session_id": sessionId
            ]
        )
        enqueue(event)
    }

    func flush() {
        queue.sync {
            let batch = eventQueue
            eventQueue.removeAll()
            sendBatch(batch)
        }
    }

    private func enqueue(_ event: AnalyticsEvent) {
        queue.async { [weak self] in
            self?.eventQueue.append(event)
            if self?.eventQueue.count ?? 0 >= 20 {
                self?.flush()
            }
        }
    }

    private func sendBatch(_ batch: [AnalyticsEvent]) {
        guard !batch.isEmpty else { return }
        guard let data = try? JSONSerialization.data(withJSONObject: batch.map { $0.dictionary }) else { return }

        var request = URLRequest(url: URL(string: "https://analytics.gula.iq/events")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = data

        URLSession.shared.dataTask(with: request).resume()
    }

    func startSession() {
        sessionId = UUID().uuidString
        trackEvent("session_start")
    }

    func endSession() {
        trackEvent("session_end")
        flush()
    }
}

struct AnalyticsEvent {
    let name: String
    let parameters: [String: Any]
    let timestamp: Date

    init(name: String, parameters: [String: Any] = [:]) {
        self.name = name
        self.parameters = parameters
        self.timestamp = Date()
    }

    var dictionary: [String: Any] {
        var dict: [String: Any] = [
            "event": name,
            "timestamp": ISO8601DateFormatter().string(from: timestamp),
            "platform": "ios",
            "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        ]
        dict.merge(parameters) { _, new in new }
        return dict
    }
}
