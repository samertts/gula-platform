import SwiftUI

struct SettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var themeManager: ThemeManager
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            Form {
                // MARK: - Profile
                Section("profile".localized) {
                    HStack(spacing: DesignTokens.Spacing.md) {
                        Circle()
                            .fill(Color.gulaPrimary)
                            .frame(width: 60, height: 60)
                            .overlay(
                                Text(viewModel.displayName.prefix(1).uppercased())
                                    .gulaTitleLarge()
                                    .foregroundColor(.white)
                            )

                        VStack(alignment: .leading, spacing: 4) {
                            Text(viewModel.displayName)
                                .gulaBodyLarge()
                                .fontWeight(.semibold)
                            Text(viewModel.email)
                                .gulaLabelSmall()
                                .foregroundColor(.gulaTextSecondary)
                            Text(viewModel.role)
                                .gulaLabelSmall()
                                .foregroundColor(.gulaPrimary)
                        }
                    }
                    .padding(.vertical, 4)
                }

                // MARK: - Appearance
                Section("appearance".localized) {
                    Picker("theme".localized, selection: Binding(
                        get: { viewModel.currentTheme },
                        set: { viewModel.toggleTheme($0) }
                    )) {
                        ForEach(AppTheme.allCases, id: \.self) { theme in
                            Text(theme.displayName).tag(theme)
                        }
                    }

                    Picker("language".localized, selection: Binding(
                        get: { viewModel.currentLanguage },
                        set: { viewModel.toggleLanguage($0) }
                    )) {
                        ForEach(AppLanguage.allCases, id: \.self) { lang in
                            Text(lang.displayName).tag(lang)
                        }
                    }

                    Toggle("high_contrast".localized, isOn: Binding(
                        get: { viewModel.highContrast },
                        set: { _ in viewModel.toggleHighContrast() }
                    ))
                    .tint(.gulaPrimary)
                }

                // MARK: - Accessibility
                Section("Accessibility") {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Text scale")
                            Spacer()
                            Text(String(format: "%.2f×", viewModel.textScale))
                                .foregroundColor(.gulaTextSecondary)
                        }
                        Slider(value: Binding(
                            get: { viewModel.textScale },
                            set: { viewModel.setTextScale($0) }
                        ), in: 0.85...2.0, step: 0.05)
                        .tint(.gulaPrimary)
                    }

                    Toggle("High contrast", isOn: Binding(
                        get: { viewModel.highContrast },
                        set: { _ in viewModel.toggleHighContrast() }
                    ))
                    .tint(.gulaPrimary)

                    Toggle("Reduced motion and flashing", isOn: Binding(
                        get: { viewModel.reducedMotion },
                        set: { _ in viewModel.toggleReducedMotion() }
                    ))
                    .tint(.gulaPrimary)

                    Toggle("Screen reader optimized", isOn: Binding(
                        get: { viewModel.screenReaderOptimized },
                        set: { _ in viewModel.toggleScreenReaderOptimized() }
                    ))
                    .tint(.gulaPrimary)

                    Toggle("Larger touch targets", isOn: Binding(
                        get: { viewModel.largerTouchTargets },
                        set: { _ in viewModel.toggleLargerTouchTargets() }
                    ))
                    .tint(.gulaPrimary)

                    Picker("Color blind safe palette", selection: Binding(
                        get: { viewModel.colorBlindMode },
                        set: { viewModel.setColorBlindMode($0) }
                    )) {
                        Text("None").tag("none")
                        Text("Protanopia-safe").tag("protanopia")
                        Text("Deuteranopia-safe").tag("deuteranopia")
                        Text("Tritanopia-safe").tag("tritanopia")
                        Text("Monochrome").tag("monochrome")
                    }

                    Toggle("Static alternatives", isOn: Binding(
                        get: { viewModel.staticAlternatives },
                        set: { _ in viewModel.toggleStaticAlternatives() }
                    ))
                    .tint(.gulaPrimary)

                    Text("Health Preferences are optional, consent-bound, and are not stored in this device's local settings.")
                        .font(.footnote)
                        .foregroundColor(.gulaTextSecondary)
                }

                // MARK: - Security
                Section("security".localized) {
                    if BiometricAuth.isAvailable {
                        Toggle(BiometricAuth.biometryType == .faceID ? "face_id".localized : "touch_id".localized,
                               isOn: Binding(
                                get: { viewModel.biometricEnabled },
                                set: { _ in viewModel.toggleBiometric() }
                               ))
                        .tint(.gulaPrimary)
                    }
                }

                // MARK: - Notifications
                Section("notifications".localized) {
                    Toggle("push_notifications".localized, isOn: Binding(
                        get: { viewModel.pushNotificationsEnabled },
                        set: { _ in viewModel.togglePushNotifications() }
                    ))
                    .tint(.gulaPrimary)
                }

                // MARK: - Sync
                Section("sync_settings".localized) {
                    Toggle("auto_sync".localized, isOn: Binding(
                        get: { viewModel.autoSyncEnabled },
                        set: { _ in viewModel.toggleAutoSync() }
                    ))
                    .tint(.gulaPrimary)

                    Toggle("sync_wifi_only".localized, isOn: Binding(
                        get: { viewModel.syncOnWifiOnly },
                        set: { _ in viewModel.toggleSyncWifiOnly() }
                    ))
                    .tint(.gulaPrimary)
                }

                // MARK: - Storage
                Section("storage".localized) {
                    HStack {
                        Text("cache".localized)
                            .gulaBodyMedium()
                        Spacer()
                        Text(viewModel.cacheSize)
                            .gulaBodyMedium()
                            .foregroundColor(.gulaTextSecondary)
                    }

                    Button("clear_cache".localized) {
                        viewModel.clearCache()
                    }
                    .gulaBodyMedium()
                    .foregroundColor(.gulaWarning)
                }

                // MARK: - About
                Section("about".localized) {
                    HStack {
                        Text("app_version".localized)
                            .gulaBodyMedium()
                        Spacer()
                        Text("\(viewModel.appVersion) (\(viewModel.buildNumber))")
                            .gulaBodyMedium()
                            .foregroundColor(.gulaTextSecondary)
                    }

                    HStack {
                        Text("app_name".localized)
                            .gulaBodyMedium()
                        Spacer()
                        Text("GULA")
                            .gulaBodyMedium()
                            .fontWeight(.bold)
                            .foregroundColor(.gulaPrimary)
                    }
                }

                // MARK: - Logout
                Section {
                    Button(role: .destructive) {
                        viewModel.logout()
                    } label: {
                        HStack {
                            Spacer()
                            Text("logout".localized)
                                .gulaBodyLarge()
                                .fontWeight(.semibold)
                            Spacer()
                        }
                    }
                }
            }
            .gulaListStyle()
            .navigationTitle("settings".localized)
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}
