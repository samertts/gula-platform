import SwiftUI
import CoreData

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var networkMonitor: NetworkMonitor
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var syncEngine: SyncEngine
    @State private var selectedTab: TabItem = .dashboard
    @State private var showOfflineBanner = false

    enum TabItem: String, CaseIterable {
        case dashboard, patients, orders, samples, results, notifications, settings
    }

    var body: some View {
        Group {
            if !authManager.isAuthenticated {
                LoginView()
                    .transition(.opacity)
            } else {
                mainView
                    .transition(.opacity)
            }
        }
        .animation(.easeInOut(duration: 0.3), value: authManager.isAuthenticated)
        .overlay(alignment: .top) {
            if !networkMonitor.isConnected && authManager.isAuthenticated {
                GulaOfflineBanner()
                    .transition(.move(edge: .top))
            }
        }
        .overlay(alignment: .bottomTrailing) {
            if syncEngine.isSyncing {
                GulaSyncIndicator()
                    .padding(.trailing, 16)
                    .padding(.bottom, 100)
            }
        }
    }

    private var mainView: some View {
        TabView(selection: $selectedTab) {
            DashboardView()
                .tabItem { tabLabel(for: .dashboard) }
                .tag(TabItem.dashboard)

            PatientListView()
                .tabItem { tabLabel(for: .patients) }
                .tag(TabItem.patients)

            OrderListView()
                .tabItem { tabLabel(for: .orders) }
                .tag(TabItem.orders)

            SampleListView()
                .tabItem { tabLabel(for: .samples) }
                .tag(TabItem.samples)

            ResultListView()
                .tabItem { tabLabel(for: .results) }
                .tag(TabItem.results)

            NotificationListView()
                .tabItem { tabLabel(for: .notifications) }
                .tag(TabItem.notifications)

            SettingsView()
                .tabItem { tabLabel(for: .settings) }
                .tag(TabItem.settings)
        }
        .tint(Color.gulaPrimary)
        .onReceive(NotificationCenter.default.publisher(for: .navigateToPatient)) { note in
            if let _ = note.userInfo?["patientId"] as? Int { selectedTab = .patients }
        }
        .onReceive(NotificationCenter.default.publisher(for: .navigateToOrder)) { note in
            if let _ = note.userInfo?["orderId"] as? Int { selectedTab = .orders }
        }
        .onReceive(NotificationCenter.default.publisher(for: .navigateToResult)) { note in
            if let _ = note.userInfo?["resultId"] as? Int { selectedTab = .results }
        }
    }

    private func tabLabel(for tab: TabItem) -> Label<Text, Image> {
        switch tab {
        case .dashboard: return Label("dashboard".localized, systemImage: "square.grid.2x2")
        case .patients: return Label("patients".localized, systemImage: "person.2")
        case .orders: return Label("orders".localized, systemImage: "list.clipboard")
        case .samples: return Label("samples".localized, systemImage: "testtube.2")
        case .results: return Label("results".localized, systemImage: "doc.text.magnifyingglass")
        case .notifications: return Label("notifications".localized, systemImage: "bell")
        case .settings: return Label("settings".localized, systemImage: "gear")
        }
    }
}
