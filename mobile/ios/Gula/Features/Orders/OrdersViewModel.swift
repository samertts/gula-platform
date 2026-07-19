import Foundation
import Combine

class OrdersViewModel: ObservableObject {
    @Published var orders: [OrderEntity] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedStatus: String?
    @Published var selectedPatientId: Int?

    private let repository = OrderRepository.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        repository.$orders
            .receive(on: DispatchQueue.main)
            .assign(to: &$orders)
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

    func filterByStatus(_ status: String?) {
        selectedStatus = status
        repository.fetchLocalOrders(status: status)
    }

    func cancelOrder(id: Int) async {
        do {
            try await repository.cancelOrder(id: id)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    var orderStatuses: [String] {
        ["all", "pending", "processing", "completed", "cancelled"]
    }
}
