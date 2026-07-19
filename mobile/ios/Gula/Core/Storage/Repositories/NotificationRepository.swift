import Foundation
import CoreData
import Combine
import UserNotifications

class NotificationRepository: ObservableObject {
    static let shared = NotificationRepository()

    @Published var notifications: [NotificationEntity] = []
    @Published var unreadCount: Int = 0

    private let context = CoreDataStack.shared.viewContext
    private let backgroundContext = CoreDataStack.shared.backgroundContext

    private init() {
        fetchLocalNotifications()
    }

    func fetchLocalNotifications() {
        let request: NSFetchRequest<NotificationEntity> = NotificationEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \NotificationEntity.createdAt, ascending: false)]
        request.fetchBatchSize = 50

        do {
            let results = try context.fetch(request)
            DispatchQueue.main.async {
                self.notifications = results
                self.unreadCount = results.filter { !$0.read }.count
            }
        } catch {
            print("[GULA] Notification fetch error: \(error.localizedDescription)")
        }
    }

    func refreshFromRemote() async throws {
        let response: NotificationListResponse = try await APIClient.shared.request(
            .listNotifications(page: 1, limit: 100, read: nil, type: nil)
        )

        backgroundContext.performAndWait {
            for item in response.items {
                let request: NSFetchRequest<NotificationEntity> = NotificationEntity.fetchRequest()
                request.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? backgroundContext.fetch(request).first {
                    existing.update(from: item)
                } else {
                    let entity = NotificationEntity(context: backgroundContext)
                    entity.update(from: item)
                }
            }
            try? backgroundContext.save()
        }
        fetchLocalNotifications()
    }

    func markAsRead(id: Int) async throws {
        let response: NotificationRecordStruct = try await APIClient.shared.request(
            .markNotificationRead(id: id)
        )

        backgroundContext.performAndWait {
            let request: NSFetchRequest<NotificationEntity> = NotificationEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                entity.read = true
                try? backgroundContext.save()
            }
        }
        fetchLocalNotifications()
    }

    func markAllAsRead() async throws {
        try await APIClient.shared.requestVoid(.markAllNotificationsRead)

        backgroundContext.performAndWait {
            let request: NSFetchRequest<NotificationEntity> = NotificationEntity.fetchRequest()
            request.predicate = NSPredicate(format: "read == NO")
            if let entities = try? backgroundContext.fetch(request) {
                for entity in entities {
                    entity.read = true
                }
                try? backgroundContext.save()
            }
        }
        fetchLocalNotifications()
    }

    func deleteNotification(id: Int) async throws {
        try await APIClient.shared.requestVoid(.deleteNotification(id: id))

        backgroundContext.performAndWait {
            let request: NSFetchRequest<NotificationEntity> = NotificationEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                backgroundContext.delete(entity)
                try? backgroundContext.save()
            }
        }
        fetchLocalNotifications()
    }

    func registerForPushNotifications() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, _ in
            if granted {
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
        }
    }

    func handleForegroundNotification(userInfo: [AnyHashable: Any]) {
        guard let type = userInfo["type"] as? String else { return }

        var title = ""
        var body = ""
        if let aps = userInfo["aps"] as? [String: Any],
           let alert = aps["alert"] as? [String: Any] {
            title = alert["title"] as? String ?? ""
            body = alert["body"] as? String ?? ""
        }

        let notificationType = type
        backgroundContext.performAndWait {
            let entity = NotificationEntity(context: backgroundContext)
            entity.id = Int64(Date().timeIntervalSince1970 * 1000)
            entity.userId = Int64(UserDefaults.standard.integer(forKey: "current_user_id"))
            entity.title = title
            entity.bodyStr = body
            entity.typeStr = notificationType
            entity.read = false
            entity.createdAt = Date()
            entity.dataPayload = try? JSONSerialization.data(withJSONObject: userInfo)
            try? backgroundContext.save()
        }
        fetchLocalNotifications()
        updateAppBadge()
    }

    func updateAppBadge() {
        UNUserNotificationCenter.current().setBadgeCount(unreadCount)
    }
}
