import UIKit
import UserNotifications
import Firebase

class GulaAppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, _ in
            if granted {
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
        }
        return true
    }

    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        Task {
            try? await APIClient.shared.registerDeviceToken(token: token, platform: "ios")
        }
    }

    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        print("[GULA] Push registration failed: \(error.localizedDescription)")
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound, .badge, .list])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        DeepLinkHandler.shared.handleNotification(userInfo)
        completionHandler()
    }

    func application(
        _ application: UIApplication,
        continue userActivity: NSUserActivity,
        restorationHandler: @escaping ([UIUserActivityRestoring]?) -> Void
    ) -> Bool {
        if userActivity.activityType == NSUserActivityTypeBrowsingWeb,
           let url = userActivity.webpageURL {
            DeepLinkHandler.shared.handleURL(url)
            return true
        }
        return false
    }

    func application(
        _ application: UIApplication,
        open url: URL,
        options: [UIApplication.OpenURLOptionsKey: Any] = [:]
    ) -> Bool {
        DeepLinkHandler.shared.handleURL(url)
        return true
    }
}

class DeepLinkHandler {
    static let shared = DeepLinkHandler()

    func handleURL(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return }
        let pathComponents = components.path.split(separator: "/").map(String.init)
        guard let first = pathComponents.first else { return }
        switch first {
        case "patient":
            if let id = pathComponents.dropFirst().first, let patientId = Int(id) {
                NotificationCenter.default.post(name: .navigateToPatient, object: nil, userInfo: ["patientId": patientId])
            }
        case "order":
            if let id = pathComponents.dropFirst().first, let orderId = Int(id) {
                NotificationCenter.default.post(name: .navigateToOrder, object: nil, userInfo: ["orderId": orderId])
            }
        case "result":
            if let id = pathComponents.dropFirst().first, let resultId = Int(id) {
                NotificationCenter.default.post(name: .navigateToResult, object: nil, userInfo: ["resultId": resultId])
            }
        default: break
        }
    }

    func handleNotification(_ userInfo: [AnyHashable: Any]) {
        guard let type = userInfo["type"] as? String else { return }
        switch type {
        case "critical_alert":
            if let resultId = userInfo["result_id"] as? Int {
                NotificationCenter.default.post(name: .navigateToResult, object: nil, userInfo: ["resultId": resultId])
            }
        case "new_result":
            if let orderId = userInfo["order_id"] as? Int {
                NotificationCenter.default.post(name: .navigateToOrder, object: nil, userInfo: ["orderId": orderId])
            }
        case "sample_update":
            if let sampleId = userInfo["sample_id"] as? Int {
                NotificationCenter.default.post(name: .navigateToSample, object: nil, userInfo: ["sampleId": sampleId])
            }
        default: break
        }
    }
}

extension Notification.Name {
    static let navigateToPatient = Notification.Name("navigateToPatient")
    static let navigateToOrder = Notification.Name("navigateToOrder")
    static let navigateToResult = Notification.Name("navigateToResult")
    static let navigateToSample = Notification.Name("navigateToSample")
}
