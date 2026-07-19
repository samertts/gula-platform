import Foundation
import Combine

class NotificationsViewModel: ObservableObject {
    @Published var notifications: [NotificationEntity] = []
    @Published var unreadCount = 0
    @Published var isLoading = false
    @Published var error: String?
    @Published var showUnreadOnly = false

    private let repository = NotificationRepository.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        repository.$notifications
            .receive(on: DispatchQueue.main)
            .assign(to: &$notifications)

        repository.$unreadCount
            .receive(on: DispatchQueue.main)
            .assign(to: &$unreadCount)
    }

    var filteredNotifications: [NotificationEntity] {
        if showUnreadOnly {
            return notifications.filter { !$0.read }
        }
        return notifications
    }

    func refresh() async {
        await MainActor.run { isLoading = true; error = nil }
        do {
            try await repository.refreshFromRemote()
            await MainActor.run { isLoading = false }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }

    func markAsRead(id: Int) async {
        do {
            try await repository.markAsRead(id: id)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    func markAllAsRead() async {
        do {
            try await repository.markAllAsRead()
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    func deleteNotification(id: Int) async {
        do {
            try await repository.deleteNotification(id: id)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    func toggleUnreadFilter() {
        showUnreadOnly.toggle()
    }
}
