import Foundation
import BackgroundTasks

class BackgroundTaskManager {
    static let shared = BackgroundTaskManager()

    private let syncEngine = SyncEngine.shared
    private let notificationRepo = NotificationRepository.shared

    private init() {}

    func registerAllTasks() {
        registerSyncTask()
        registerCleanupTask()
        registerRefreshTask()
    }

    private func registerSyncTask() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.gula.sync", using: nil) { task in
            self.handleSyncTask(task as! BGAppRefreshTask)
        }
    }

    private func registerCleanupTask() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.gula.cleanup", using: nil) { task in
            self.handleCleanupTask(task as! BGProcessingTask)
        }
    }

    private func registerRefreshTask() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.gula.refresh", using: nil) { task in
            self.handleRefreshTask(task as! BGAppRefreshTask)
        }
    }

    func scheduleSync() {
        let request = BGAppRefreshTaskRequest(identifier: "com.gula.sync")
        request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            print("[GULA] BGTask schedule sync error: \(error.localizedDescription)")
        }
    }

    func scheduleCleanup() {
        let request = BGProcessingTaskRequest(identifier: "com.gula.cleanup")
        request.earliestBeginDate = Date(timeIntervalSinceNow: 2 * 3600)
        request.requiresNetworkConnectivity = false
        request.requiresExternalPower = false
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            print("[GULA] BGTask schedule cleanup error: \(error.localizedDescription)")
        }
    }

    func scheduleDataRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: "com.gula.refresh")
        request.earliestBeginDate = Date(timeIntervalSinceNow: 30 * 60)
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            print("[GULA] BGTask schedule refresh error: \(error.localizedDescription)")
        }
    }

    func handleSyncTask(_ task: BGAppRefreshTask) {
        scheduleSync()

        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }

        Task {
            await syncEngine.syncAll()
            await MainActor.run {
                UIApplication.shared.applicationIconBadgeNumber = NotificationRepository.shared.unreadCount
            }
            task.setTaskCompleted(success: true)
        }
    }

    func handleCleanupTask(_ task: BGProcessingTask) {
        scheduleCleanup()

        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }

        let context = CoreDataStack.shared.backgroundContext
        context.perform {
            let fetchRequest: NSFetchRequest<NSFetchRequestResult> = NotificationEntity.fetchRequest()
            let thirtyDaysAgo = Date().addingTimeInterval(-30 * 24 * 3600)
            fetchRequest.predicate = NSPredicate(format: "createdAt < %@ AND read == YES", thirtyDaysAgo as NSDate)
            let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
            deleteRequest.resultType = .resultTypeObjectIDs

            do {
                if let result = try context.execute(deleteRequest) as? NSBatchDeleteResult,
                   let objectIDs = result.result as? [NSManagedObjectID] {
                    NSManagedObjectContext.mergeChanges(
                        fromRemoteContextSave: [NSDeletedObjectsKey: objectIDs],
                        into: [CoreDataStack.shared.persistentContainer.viewContext]
                    )
                }
            } catch {
                print("[GULA] Background cleanup error: \(error.localizedDescription)")
            }
            task.setTaskCompleted(success: true)
        }
    }

    func handleRefreshTask(_ task: BGAppRefreshTask) {
        scheduleDataRefresh()

        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }

        Task {
            do {
                try await PatientRepository.shared.refreshFromRemote()
                try await OrderRepository.shared.refreshFromRemote()
                task.setTaskCompleted(success: true)
            } catch {
                task.setTaskCompleted(success: false)
            }
        }
    }

    func cancelAllTasks() {
        BGTaskScheduler.shared.cancelAllTaskRequests()
    }
}
