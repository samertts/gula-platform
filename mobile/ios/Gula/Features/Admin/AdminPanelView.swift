import SwiftUI

struct AdminPanelView: View {
    @State private var labUsers: [LabUser] = []
    @State private var labs: [Lab] = []
    @State private var isLoading = false
    @State private var error: String?
    @State private var selectedTab: AdminTab = .users
    @Environment(\.locale) var locale

    enum AdminTab: String, CaseIterable {
        case users, labs, system

        var displayName: String {
            switch self {
            case .users: return "users".localized
            case .labs: return "labs".localized
            case .system: return "system".localized
            }
        }
    }

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                Picker("", selection: $selectedTab) {
                    ForEach(AdminTab.allCases, id: \.self) { tab in
                        Text(tab.displayName).tag(tab)
                    }
                }
                .pickerStyle(SegmentedPickerStyle())
                .padding()

                if isLoading {
                    GulaPageLoadingView()
                } else if let error = error {
                    GulaErrorView(message: error, retryAction: { Task { await loadData() } })
                } else {
                    switch selectedTab {
                    case .users:
                        usersView
                    case .labs:
                        labsView
                    case .system:
                        systemView
                    }
                }
            }
            .navigationTitle("admin_panel".localized)
            .task { await loadData() }
            .gulaPullToRefresh(isRefreshing: isLoading) {
                Task { await loadData() }
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }

    private var usersView: some View {
        List {
            ForEach(labUsers) { user in
                HStack(spacing: DesignTokens.Spacing.md) {
                    Circle()
                        .fill(Color.gulaSecondary)
                        .frame(width: 40, height: 40)
                        .overlay(Text(user.name.prefix(1).uppercased()).foregroundColor(.white))

                    VStack(alignment: .leading, spacing: 2) {
                        Text(user.name)
                            .gulaBodyMedium()
                            .fontWeight(.semibold)
                        Text(user.email)
                            .gulaLabelSmall()
                            .foregroundColor(.gulaTextSecondary)
                        Text(user.role)
                            .gulaLabelSmall()
                            .foregroundColor(.gulaPrimary)
                    }

                    Spacer()

                    if user.isActive {
                        Circle().fill(Color.gulaSuccess).frame(width: 8, height: 8)
                    } else {
                        Circle().fill(Color.gulaError).frame(width: 8, height: 8)
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .gulaListStyle()
    }

    private var labsView: some View {
        List {
            ForEach(labs) { lab in
                VStack(alignment: .leading, spacing: 4) {
                    Text(lab.name)
                        .gulaBodyMedium()
                        .fontWeight(.semibold)
                    if let city = lab.city {
                        Text(city)
                            .gulaLabelSmall()
                            .foregroundColor(.gulaTextSecondary)
                    }
                    GulaBadge(.status(lab.status), size: .small)
                }
                .padding(.vertical, 4)
            }
        }
        .gulaListStyle()
    }

    private var systemView: some View {
        List {
            Section("system_info".localized) {
                LabeledContent("version".localized, value: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "")
                LabeledContent("build".localized, value: Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "")
            }

            Section("actions".localized) {
                Button("trigger_maintenance".localized) {
                    Task { await triggerMaintenance() }
                }
                .foregroundColor(.gulaWarning)
            }
        }
        .gulaListStyle()
    }

    private func loadData() async {
        await MainActor.run { isLoading = true; error = nil }
        do {
            async let usersResponse: UserListResponse = APIClient.shared.request(.adminListUsers(page: 1, limit: 100))
            async let labsResponse: LabListResponse = APIClient.shared.request(.adminListLabs(page: 1, limit: 100))

            let (users, labs) = try await (usersResponse, labsResponse)

            await MainActor.run {
                labUsers = users.items.map { LabUser(id: $0.id, name: $0.name, email: $0.email, role: $0.role, isActive: $0.isActive) }
                self.labs = labs.items.map { Lab(id: $0.id, name: $0.name, city: $0.city, status: $0.status) }
                isLoading = false
            }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }

    private func triggerMaintenance() async {
        do {
            try await APIClient.shared.requestVoid(
                .unknown(path: "/admin/maintenance"),
                body: ["type": "cache_cleanup", "reason": "Manual trigger from iOS app"]
            )
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }
}

struct LabUser: Identifiable {
    let id: Int
    let name: String
    let email: String
    let role: String
    let isActive: Bool
}

struct Lab: Identifiable {
    let id: Int
    let name: String
    let city: String?
    let status: String
}

struct UserListResponse: Decodable {
    let items: [UserItemResponse]
    let pagination: PaginationMetaResponse
}

struct UserItemResponse: Decodable {
    let id: Int
    let name: String
    let email: String
    let role: String
    let isActive: Bool
}

struct LabListResponse: Decodable {
    let items: [LabItemResponse]
    let pagination: PaginationMetaResponse
}

struct LabItemResponse: Decodable {
    let id: Int
    let name: String
    let city: String?
    let status: String
}
