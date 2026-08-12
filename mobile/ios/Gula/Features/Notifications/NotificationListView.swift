import SwiftUI

struct NotificationListView: View {
    @StateObject private var viewModel = NotificationsViewModel()
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                if viewModel.isLoading && viewModel.notifications.isEmpty {
                    GulaPageLoadingView()
                } else if viewModel.filteredNotifications.isEmpty {
                    GulaEmptyState(
                        title: "no_notifications".localized,
                        message: "no_notifications_message".localized,
                        imageName: "bell.slash"
                    )
                } else {
                    List {
                        ForEach(viewModel.filteredNotifications, id: \.id) { notification in
                            notificationRow(notification)
                                .contentShape(Rectangle())
                                .onTapGesture {
                                    Task { await viewModel.markAsRead(id: Int(notification.id)) }
                                }
                                .swipeActions(edge: .trailing) {
                                    Button(role: .destructive) {
                                        Task { await viewModel.deleteNotification(id: Int(notification.id)) }
                                    } label: {
                                        Label("delete".localized, systemImage: "trash")
                                    }
                                }
                        }
                    }
                    .gulaListStyle()
                }
            }
            .gulaPullToRefresh(isRefreshing: viewModel.isLoading) {
                Task { await viewModel.refresh() }
            }
            .navigationTitle("notifications".localized)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: DesignTokens.Spacing.sm) {
                        if viewModel.unreadCount > 0 {
                            Button("mark_all_read".localized) {
                                Task { await viewModel.markAllAsRead() }
                            }
                            .gulaLabelSmall()
                        }
                        Button(action: { viewModel.toggleUnreadFilter() }) {
                            Image(systemName: viewModel.showUnreadOnly ? "bell.fill" : "bell")
                                .foregroundColor(viewModel.showUnreadOnly ? .gulaPrimary : .gulaTextTertiary)
                        }
                    }
                }
            }
            .task { await viewModel.refresh() }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }

    private func notificationRow(_ notification: NotificationEntity) -> some View {
        HStack(spacing: DesignTokens.Spacing.md) {
            Circle()
                .fill(notification.read ? Color.gulaSurfaceSecondary : Color.gulaPrimary)
                .frame(width: 44, height: 44)
                .overlay(
                    Image(systemName: notificationIcon(notification.typeStr))
                        .foregroundColor(notification.read ? .gulaTextTertiary : .white)
                        .font(.system(size: 18))
                )

            VStack(alignment: .leading, spacing: 4) {
                Text(notification.title)
                    .gulaBodyMedium()
                    .fontWeight(notification.read ? .regular : .semibold)
                    .foregroundColor(.gulaTextPrimary)
                    .lineLimit(2)

                Text(notification.bodyStr)
                    .gulaBodySmall()
                    .foregroundColor(.gulaTextSecondary)
                    .lineLimit(1)

                if let createdAt = notification.createdAt {
                    Text(createdAt.formatted(date: .abbreviated, time: .shortened))
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextTertiary)
                }
            }

            Spacer()

            if !notification.read {
                Circle()
                    .fill(Color.gulaPrimary)
                    .frame(width: 8, height: 8)
            }
        }
        .padding(.vertical, DesignTokens.Spacing.xxs)
        .background(notification.read ? Color.clear : Color.gulaPrimary.opacity(0.03))
    }

    private func notificationIcon(_ type: String) -> String {
        switch type.lowercased() {
        case "critical_alert": return "exclamationmark.triangle.fill"
        case "new_result": return "doc.text.fill"
        case "sample_update": return "testtube.2"
        case "order_update": return "list.clipboard"
        case "system": return "gearshape.fill"
        default: return "bell.fill"
        }
    }
}
