import Foundation
import BackgroundTasks

class NetworkSynchronizer {
    static let shared = NetworkSynchronizer()

    private let syncEngine = SyncEngine.shared
    private let networkMonitor = NetworkMonitor()

    private init() {}

    func scheduleBackgroundSync() {
        let request = BGAppRefreshTaskRequest(identifier: "com.gula.sync")
        request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
        try? BGTaskScheduler.shared.submit(request)
    }

    func handleBackgroundSync(task: BGAppRefreshTask) {
        scheduleBackgroundSync()

        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }

        Task {
            await syncEngine.syncAll()
            task.setTaskCompleted(success: true)
        }
    }

    func handleBackgroundCleanup(task: BGProcessingTask) {
        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }

        Task {
            SyncQueue.shared.clearCompleted()
            SyncQueue.shared.clearFailed()
            let context = CoreDataStack.shared.backgroundContext
            context.perform {
                let fetchRequest: NSFetchRequest<NSFetchRequestResult> = NotificationEntity.fetchRequest()
                let thirtyDaysAgo = Date().addingTimeInterval(-30 * 24 * 3600)
                fetchRequest.predicate = NSPredicate(format: "createdAt < %@ AND read == YES", thirtyDaysAgo as NSDate)
                let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
                try? context.execute(deleteRequest)
                try? context.save()
            }
            task.setTaskCompleted(success: true)
        }
    }

    func startObserving() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleNetworkChange),
            name: .networkStatusChanged,
            object: nil
        )
    }

    @objc private func handleNetworkChange() {
        if networkMonitor.isConnected {
            Task {
                await syncEngine.syncAll()
            }
        }
    }
}

extension Notification.Name {
    static let networkStatusChanged = Notification.Name("networkStatusChanged")
}
