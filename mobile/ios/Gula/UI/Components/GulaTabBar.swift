import SwiftUI

struct GulaTabItem: Identifiable {
    let id: String
    let title: String
    let icon: String
    let badge: Int?
    let role: UserRole?

    init(id: String, title: String, icon: String, badge: Int? = nil, role: UserRole? = nil) {
        self.id = id
        self.title = title
        self.icon = icon
        self.badge = badge
        self.role = role
    }
}

struct GulaTabBar: View {
    @Binding var selectedTab: String
    let items: [GulaTabItem]
    @Environment(\.locale) var locale

    var body: some View {
        HStack(spacing: 0) {
            ForEach(items) { item in
                Button(action: { selectedTab = item.id }) {
                    VStack(spacing: 4) {
                        ZStack(alignment: .topTrailing) {
                            Image(systemName: item.icon)
                                .font(.system(size: 22))
                                .foregroundColor(selectedTab == item.id ? .gulaPrimary : .gulaTextTertiary)

                            if let badge = item.badge, badge > 0 {
                                GulaBadge(.count(badge), size: .small)
                                    .offset(x: 8, y: -4)
                            }
                        }

                        Text(item.title)
                            .gulaLabelSmall()
                            .foregroundColor(selectedTab == item.id ? .gulaPrimary : .gulaTextTertiary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .background(Color.gulaSurfacePrimary)
        .overlay(Divider(), alignment: .top)
    }
}

struct RoleBasedTabBar: View {
    @Binding var selectedTab: String
    @EnvironmentObject var authManager: AuthManager

    var items: [GulaTabItem] {
        guard let role = authManager.currentUser?.role else { return [] }

        var tabs: [GulaTabItem] = [
            GulaTabItem(id: "dashboard", title: "dashboard".localized, icon: "square.grid.2x2")
        ]

        switch role {
        case .masterAdmin, .ministryAdmin, .provinceAdmin:
            tabs += [
                GulaTabItem(id: "patients", title: "patients".localized, icon: "person.2"),
                GulaTabItem(id: "orders", title: "orders".localized, icon: "list.clipboard"),
                GulaTabItem(id: "samples", title: "samples".localized, icon: "testtube.2"),
                GulaTabItem(id: "results", title: "results".localized, icon: "doc.text.magnifyingglass"),
                GulaTabItem(id: "admin", title: "admin".localized, icon: "shield"),
            ]
        case .labAdmin:
            tabs += [
                GulaTabItem(id: "patients", title: "patients".localized, icon: "person.2"),
                GulaTabItem(id: "orders", title: "orders".localized, icon: "list.clipboard"),
                GulaTabItem(id: "samples", title: "samples".localized, icon: "testtube.2"),
                GulaTabItem(id: "results", title: "results".localized, icon: "doc.text.magnifyingglass"),
            ]
        case .technician:
            tabs += [
                GulaTabItem(id: "samples", title: "samples".localized, icon: "testtube.2"),
                GulaTabItem(id: "results", title: "results".localized, icon: "doc.text.magnifyingglass"),
            ]
        case .doctor:
            tabs += [
                GulaTabItem(id: "patients", title: "patients".localized, icon: "person.2"),
                GulaTabItem(id: "orders", title: "orders".localized, icon: "list.clipboard"),
                GulaTabItem(id: "results", title: "results".localized, icon: "doc.text.magnifyingglass"),
            ]
        case .receptionist:
            tabs += [
                GulaTabItem(id: "patients", title: "patients".localized, icon: "person.2"),
                GulaTabItem(id: "orders", title: "orders".localized, icon: "list.clipboard"),
            ]
        default:
            tabs += [
                GulaTabItem(id: "patients", title: "patients".localized, icon: "person.2"),
                GulaTabItem(id: "results", title: "results".localized, icon: "doc.text.magnifyingglass"),
            ]
        }

        tabs += [
            GulaTabItem(id: "notifications", title: "notifications".localized, icon: "bell",
                       badge: NotificationRepository.shared.unreadCount),
            GulaTabItem(id: "settings", title: "settings".localized, icon: "gear"),
        ]

        return tabs
    }

    var body: some View {
        GulaTabBar(selectedTab: $selectedTab, items: items)
    }
}
