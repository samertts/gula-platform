import Foundation
import Combine

class SettingsViewModel: ObservableObject {
    @Published var displayName: String = ""
    @Published var email: String = ""
    @Published var role: String = ""

    @Published var currentTheme: AppTheme = .system
    @Published var currentLanguage: AppLanguage = .english
    @Published var highContrast: Bool = false
    @Published var textScale: Double = 1.0
    @Published var reducedMotion: Bool = false
    @Published var screenReaderOptimized: Bool = false
    @Published var largerTouchTargets: Bool = false
    @Published var colorBlindMode: String = "none"
    @Published var staticAlternatives: Bool = true
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
        textScale = min(max(UserDefaults.standard.double(forKey: "accessibility_text_scale"), 0.85), 2.0)
        if textScale == 0 { textScale = 1.0 }
        reducedMotion = UserDefaults.standard.bool(forKey: "accessibility_reduced_motion")
        screenReaderOptimized = UserDefaults.standard.bool(forKey: "accessibility_screen_reader")
        largerTouchTargets = UserDefaults.standard.bool(forKey: "accessibility_larger_touch_targets")
        colorBlindMode = UserDefaults.standard.string(forKey: "accessibility_color_blind_mode") ?? "none"
        staticAlternatives = UserDefaults.standard.object(forKey: "accessibility_static_alternatives") as? Bool ?? true
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

    func setTextScale(_ value: Double) {
        textScale = min(max(value, 0.85), 2.0)
        UserDefaults.standard.set(textScale, forKey: "accessibility_text_scale")
    }

    func toggleReducedMotion() {
        reducedMotion.toggle()
        UserDefaults.standard.set(reducedMotion, forKey: "accessibility_reduced_motion")
    }

    func toggleScreenReaderOptimized() {
        screenReaderOptimized.toggle()
        UserDefaults.standard.set(screenReaderOptimized, forKey: "accessibility_screen_reader")
    }

    func toggleLargerTouchTargets() {
        largerTouchTargets.toggle()
        UserDefaults.standard.set(largerTouchTargets, forKey: "accessibility_larger_touch_targets")
    }

    func setColorBlindMode(_ value: String) {
        let allowed = ["none", "protanopia", "deuteranopia", "tritanopia", "monochrome"]
        colorBlindMode = allowed.contains(value) ? value : "none"
        UserDefaults.standard.set(colorBlindMode, forKey: "accessibility_color_blind_mode")
    }

    func toggleStaticAlternatives() {
        staticAlternatives.toggle()
        UserDefaults.standard.set(staticAlternatives, forKey: "accessibility_static_alternatives")
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
