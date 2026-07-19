import Foundation
import Combine

class SettingsViewModel: ObservableObject {
    @Published var displayName: String = ""
    @Published var email: String = ""
    @Published var role: String = ""

    @Published var currentTheme: AppTheme = .system
    @Published var currentLanguage: AppLanguage = .english
    @Published var highContrast: Bool = false
    @Published var biometricEnabled: Bool = false
    @Published var pushNotificationsEnabled = true
    @Published var syncOnWifiOnly = false
    @Published var autoSyncEnabled = true

    @Published var appVersion: String = ""
    @Published var buildNumber: String = ""
    @Published var cacheSize: String = ""

    private let authManager = AuthManager.shared
    private let themeManager = ThemeManager.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        loadSettings()
    }

    func loadSettings() {
        displayName = authManager.currentUser?.name ?? ""
        email = authManager.currentUser?.email ?? ""
        role = authManager.currentUser?.role.displayName ?? ""
        currentTheme = themeManager.theme
        currentLanguage = themeManager.language
        highContrast = themeManager.highContrast
        biometricEnabled = authManager.biometricEnabled

        appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        buildNumber = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
        pushNotificationsEnabled = UserDefaults.standard.bool(forKey: "push_notifications_enabled")
        syncOnWifiOnly = UserDefaults.standard.bool(forKey: "sync_wifi_only")
        autoSyncEnabled = UserDefaults.standard.bool(forKey: "auto_sync_enabled")

        calculateCacheSize()
    }

    func toggleTheme(_ theme: AppTheme) {
        currentTheme = theme
        themeManager.theme = theme
        UserDefaults.standard.set(theme.rawValue, forKey: "app_theme")
    }

    func toggleLanguage(_ language: AppLanguage) {
        currentLanguage = language
        themeManager.language = language
        UserDefaults.standard.set(language.rawValue, forKey: "app_language")
    }

    func toggleHighContrast() {
        highContrast.toggle()
        themeManager.highContrast = highContrast
    }

    func toggleBiometric() {
        biometricEnabled.toggle()
        if biometricEnabled {
            if let email = KeychainManager.shared.get(key: "session_email") {
                authManager.enableBiometric(email: email, password: "")
            }
        } else {
            authManager.disableBiometric()
        }
    }

    func togglePushNotifications() {
        pushNotificationsEnabled.toggle()
        UserDefaults.standard.set(pushNotificationsEnabled, forKey: "push_notifications_enabled")
        if pushNotificationsEnabled {
            NotificationRepository.shared.registerForPushNotifications()
        } else {
            UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
        }
    }

    func toggleSyncWifiOnly() {
        syncOnWifiOnly.toggle()
        UserDefaults.standard.set(syncOnWifiOnly, forKey: "sync_wifi_only")
    }

    func toggleAutoSync() {
        autoSyncEnabled.toggle()
        UserDefaults.standard.set(autoSyncEnabled, forKey: "auto_sync_enabled")
        if autoSyncEnabled {
            BackgroundTaskManager.shared.scheduleSync()
        } else {
            BackgroundTaskManager.shared.cancelAllTasks()
        }
    }

    func clearCache() {
        let cacheURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        if let contents = try? FileManager.default.contentsOfDirectory(at: cacheURL, includingPropertiesForKeys: nil) {
            for url in contents {
                try? FileManager.default.removeItem(at: url)
            }
        }
        calculateCacheSize()
    }

    func logout() {
        authManager.logout()
    }

    private func calculateCacheSize() {
        let cacheURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        if let contents = try? FileManager.default.contentsOfDirectory(at: cacheURL, includingPropertiesForKeys: [.fileSizeKey]) {
            let totalSize = contents.reduce(0) { sum, url in
                let size = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
                return sum + size
            }
            cacheSize = ByteCountFormatter.string(fromByteCount: Int64(totalSize), countStyle: .file)
        } else {
            cacheSize = "0 KB"
        }
    }
}
