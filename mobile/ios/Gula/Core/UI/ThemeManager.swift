import SwiftUI
import Combine

enum AppTheme: String, CaseIterable {
    case system
    case light
    case dark

    var displayName: String {
        switch self {
        case .system: return "theme_system".localized
        case .light: return "theme_light".localized
        case .dark: return "theme_dark".localized
        }
    }
}

enum AppLanguage: String, CaseIterable {
    case english = "en"
    case arabic = "ar"

    var displayName: String {
        switch self {
        case .english: return "English"
        case .arabic: return "العربية"
        }
    }

    var isRTL: Bool {
        self == .arabic
    }
}

class ThemeManager: ObservableObject {
    @Published var theme: AppTheme = .system {
        didSet {
            UserDefaults.standard.set(theme.rawValue, forKey: "app_theme")
            updateColorScheme()
        }
    }

    @Published var language: AppLanguage = .english {
        didSet {
            UserDefaults.standard.set(language.rawValue, forKey: "app_language")
            updateLayoutDirection()
        }
    }

    @Published var highContrast: Bool = false {
        didSet {
            UserDefaults.standard.set(highContrast, forKey: "high_contrast")
        }
    }

    @Published var colorScheme: ColorScheme? = nil
    @Published var layoutDirection: LayoutDirection = .leftToRight

    private init() {
        loadPreferences()
    }

    static let shared = ThemeManager()

    private func loadPreferences() {
        if let themeRaw = UserDefaults.standard.string(forKey: "app_theme"),
           let savedTheme = AppTheme(rawValue: themeRaw) {
            theme = savedTheme
        }

        if let langRaw = UserDefaults.standard.string(forKey: "app_language"),
           let savedLang = AppLanguage(rawValue: langRaw) {
            language = savedLang
        }

        highContrast = UserDefaults.standard.bool(forKey: "high_contrast")
        updateColorScheme()
        updateLayoutDirection()

        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene {
            for window in windowScene.windows {
                window.overrideUserInterfaceStyle = colorSchemeToUIUserInterfaceStyle(colorScheme)
            }
        }
    }

    private func updateColorScheme() {
        switch theme {
        case .system:
            colorScheme = nil
        case .light:
            colorScheme = .light
        case .dark:
            colorScheme = .dark
        }
    }

    private func updateLayoutDirection() {
        layoutDirection = language.isRTL ? .rightToLeft : .leftToRight

        UIView.appearance().semanticContentAttribute = language.isRTL ? .forceRightToLeft : .forceLeftToRight
        UISearchBar.appearance().semanticContentAttribute = language.isRTL ? .forceRightToLeft : .forceLeftToRight
        UITextField.appearance().semanticContentAttribute = language.isRTL ? .forceRightToLeft : .forceLeftToRight
    }

    private func colorSchemeToUIUserInterfaceStyle(_ scheme: ColorScheme?) -> UIUserInterfaceStyle {
        switch scheme {
        case .light: return .light
        case .dark: return .dark
        case nil: return .unspecified
        }
    }

    func toggleLanguage() {
        language = language == .arabic ? .english : .arabic
    }

    func toggleTheme() {
        switch theme {
        case .system: theme = .light
        case .light: theme = .dark
        case .dark: theme = .system
        }
    }

    var isRTL: Bool {
        language == .arabic
    }

    var localizedDirection: Locale.LanguageDirection {
        isRTL ? .rightToLeft : .leftToRight
    }
}
