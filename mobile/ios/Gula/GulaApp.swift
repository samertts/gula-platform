import SwiftUI
import CoreData
import UserNotifications
import BackgroundTasks

@main
struct GulaApp: App {
    @UIApplicationDelegateAdaptor(GulaAppDelegate.self) var appDelegate
    @StateObject private var themeManager = ThemeManager.shared
    @StateObject private var networkMonitor = NetworkMonitor()
    @StateObject private var authManager = AuthManager.shared
    @StateObject private var syncEngine = SyncEngine.shared

    let coreDataStack = CoreDataStack.shared

    var body: some Scene {
        WindowGroup {
            IOSUpdateGate {
                ContentView()
                    .environmentObject(themeManager)
                    .environmentObject(networkMonitor)
                    .environmentObject(authManager)
                    .environmentObject(syncEngine)
                    .environment(\.managedObjectContext, coreDataStack.viewContext)
                    .environment(\.layoutDirection, themeManager.layoutDirection)
                    .preferredColorScheme(themeManager.colorScheme)
                    .onAppear {
                        registerBackgroundTasks()
                        UNUserNotificationCenter.current().delegate = appDelegate
                    }
            }
        }
    }

    private func registerBackgroundTasks() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.gula.sync", using: nil) { task in
            BackgroundTaskManager.shared.handleSyncTask(task as! BGAppRefreshTask)
        }
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.gula.cleanup", using: nil) { task in
            BackgroundTaskManager.shared.handleCleanupTask(task as! BGProcessingTask)
        }
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.gula.refresh", using: nil) { task in
            BackgroundTaskManager.shared.handleRefreshTask(task as! BGAppRefreshTask)
        }
    }
}
