import Foundation
import Combine

class ResultsViewModel: ObservableObject {
    @Published var results: [ResultEntity] = []
    @Published var criticalResults: [ResultEntity] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedStatus: String?
    @Published var showCriticalOnly = false

    private let repository = ResultRepository.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        repository.$results
            .receive(on: DispatchQueue.main)
            .assign(to: &$results)

        repository.$criticalResults
            .receive(on: DispatchQueue.main)
            .assign(to: &$criticalResults)
    }

    var resultStatuses: [String] {
        ["all", "pending", "completed", "verified", "rejected"]
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
        repository.fetchLocalResults(status: status)
    }

    func toggleCriticalFilter() {
        showCriticalOnly.toggle()
        if showCriticalOnly {
            repository.fetchCriticalResults()
        }
    }

    func verifyResult(id: Int) async {
        do {
            try await repository.verifyResult(id: id)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    func flagCritical(id: Int) async {
        do {
            try await repository.flagCritical(id: id)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }
}
