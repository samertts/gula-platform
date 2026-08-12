import Foundation
import Combine

class DashboardViewModel: ObservableObject {
    @Published var patientCount = 0
    @Published var ordersToday = 0
    @Published var pendingResults = 0
    @Published var criticalAlerts = 0
    @Published var samplesToday = 0
    @Published var isLoading = false
    @Published var error: String?
    @Published var recentOrders: [OrderEntity] = []
    @Published var criticalResults: [ResultEntity] = []
    @Published var pendingSamples: [SampleEntity] = []

    private let patientRepo = PatientRepository.shared
    private let orderRepo = OrderRepository.shared
    private let sampleRepo = SampleRepository.shared
    private let resultRepo = ResultRepository.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        loadLocalData()
        observeChanges()
    }

    func loadLocalData() {
        patientCount = patientRepo.patientCount
        ordersToday = orderRepo.todayCount
        pendingResults = resultRepo.pendingCount
        criticalAlerts = resultRepo.criticalCount
        samplesToday = sampleRepo.todayCollectionCount
        criticalResults = resultRepo.criticalResults

        let recentRequest: NSFetchRequest<OrderEntity> = OrderEntity.fetchRequest()
        recentRequest.sortDescriptors = [NSSortDescriptor(keyPath: \OrderEntity.createdAt, ascending: false)]
        recentRequest.fetchLimit = 5
        recentOrders = (try? CoreDataStack.shared.viewContext.fetch(recentRequest)) ?? []

        let pendingSampleRequest: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
        pendingSampleRequest.predicate = NSPredicate(format: "status == %@", "collected")
        pendingSampleRequest.sortDescriptors = [NSSortDescriptor(keyPath: \SampleEntity.collectedAt, ascending: false)]
        pendingSampleRequest.fetchLimit = 5
        pendingSamples = (try? CoreDataStack.shared.viewContext.fetch(pendingSampleRequest)) ?? []
    }

    func refresh() async {
        await MainActor.run { isLoading = true; error = nil }

        do {
            try await patientRepo.refreshFromRemote()
            try await orderRepo.refreshFromRemote()
            try await sampleRepo.refreshFromRemote()
            try await resultRepo.refreshFromRemote()

            await MainActor.run {
                loadLocalData()
                isLoading = false
            }
        } catch {
            await MainActor.run {
                self.error = error.localizedDescription
                self.isLoading = false
            }
        }
    }

    private func observeChanges() {
        patientRepo.$patients
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in self?.loadLocalData() }
            .store(in: &cancellables)

        resultRepo.$criticalResults
            .receive(on: DispatchQueue.main)
            .sink { [weak self] results in
                self?.criticalResults = results
                self?.criticalAlerts = results.count
            }
            .store(in: &cancellables)
    }
}
