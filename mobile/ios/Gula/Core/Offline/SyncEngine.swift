import Foundation
import Combine
import CoreData

class SyncEngine: ObservableObject {
    static let shared = SyncEngine()

    @Published var isSyncing = false
    @Published var lastSyncDate: Date?
    @Published var syncProgress: Double = 0
    @Published var syncError: String?

    private let syncQueue = SyncQueue.shared
    private let conflictResolver = ConflictResolver.shared
    private let networkMonitor = NetworkMonitor()
    private var cancellables = Set<AnyCancellable>()
    private let syncInterval: TimeInterval = 30
    private let context = CoreDataStack.shared.backgroundContext

    private init() {
        setupObservers()
    }

    private func setupObservers() {
        networkMonitor.$isConnected
            .dropFirst()
            .sink { [weak self] isConnected in
                if isConnected {
                    Task { await self?.processQueue() }
                }
            }
            .store(in: &cancellables)

        NotificationCenter.default.publisher(for: .syncRequested)
            .sink { [weak self] _ in
                Task { await self?.processQueue() }
            }
            .store(in: &cancellables)
    }

    func enqueueSync(operation: SyncOperation) {
        syncQueue.enqueue(operation)
        if networkMonitor.isConnected {
            Task { await processQueue() }
        }
    }

    func syncAll() async {
        guard !isSyncing else { return }
        await MainActor.run { isSyncing = true; syncError = nil }

        do {
            try await syncPatients()
            try await syncOrders()
            try await syncSamples()
            try await syncResults()
            try await syncNotifications()
            await processQueue()

            await MainActor.run {
                lastSyncDate = Date()
                isSyncing = false
                syncProgress = 1.0
            }
        } catch {
            await MainActor.run {
                syncError = error.localizedDescription
                isSyncing = false
            }
        }
    }

    func processQueue() async {
        guard networkMonitor.isConnected, !isSyncing else { return }

        await MainActor.run { isSyncing = true }

        while let operation = syncQueue.nextPending() {
            guard networkMonitor.isConnected else { break }

            syncQueue.markCompleted(id: operation.id)

            do {
                try await performOperation(operation)
                syncQueue.markCompleted(id: operation.id)
            } catch let error as APIError {
                if case .conflict = error {
                    syncQueue.markConflict(id: operation.id, error: error.localizedDescription)
                } else if case .authentication = error {
                    syncQueue.markFailed(id: operation.id, error: error.localizedDescription)
                    break
                } else {
                    syncQueue.markFailed(id: operation.id, error: error.localizedDescription)
                }
            } catch {
                syncQueue.markFailed(id: operation.id, error: error.localizedDescription)
            }

            await MainActor.run {
                let total = Double(syncQueue.operations.count)
                let processed = total - Double(syncQueue.pendingCount)
                syncProgress = total > 0 ? processed / total : 1.0
            }
        }

        await MainActor.run { isSyncing = false }
    }

    private func performOperation(_ operation: SyncOperation) async throws {
        switch operation.type {
        case .create:
            let _: EmptyResponse = try await APIClient.shared.request(operation.endpoint, body: operation.body)
        case .update:
            let _: EmptyResponse = try await APIClient.shared.request(operation.endpoint, body: operation.body)
        case .delete:
            try await APIClient.shared.requestVoid(operation.endpoint)
        }
    }

    private func syncPatients() async throws {
        let page = 1
        let response: PatientListResponse = try await APIClient.shared.request(
            .listPatients(page: page, limit: 100, search: nil, gender: nil, status: nil)
        )
        await MainActor.run {
            importPatients(response.items)
        }
    }

    private func syncOrders() async throws {
        let response: OrderListResponse = try await APIClient.shared.request(
            .listOrders(page: 1, limit: 100, patientId: nil, status: nil)
        )
        await MainActor.run {
            importOrders(response.items)
        }
    }

    private func syncSamples() async throws {
        let response: SampleListResponse = try await APIClient.shared.request(
            .listSamples(page: 1, limit: 100, status: nil, type: nil)
        )
        await MainActor.run {
            importSamples(response.items)
        }
    }

    private func syncResults() async throws {
        let response: ResultListResponse = try await APIClient.shared.request(
            .listResults(page: 1, limit: 100, patientId: nil, status: nil, isCritical: nil)
        )
        await MainActor.run {
            importResults(response.items)
        }
    }

    private func syncNotifications() async throws {
        let response: NotificationListResponse = try await APIClient.shared.request(
            .listNotifications(page: 1, limit: 100, read: nil, type: nil)
        )
        await MainActor.run {
            importNotifications(response.items)
        }
    }

    private func importPatients(_ items: [PatientResponse]) {
        let context = self.context
        context.performAndWait {
            for item in items {
                let fetchRequest = PatientEntity.fetchRequest()
                fetchRequest.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? context.fetch(fetchRequest).first {
                    existing.update(from: item)
                } else {
                    let entity = PatientEntity(context: context)
                    entity.update(from: item)
                }
            }
            try? context.save()
        }
    }

    private func importOrders(_ items: [OrderResponse]) {
        let context = self.context
        context.performAndWait {
            for item in items {
                let fetchRequest = OrderEntity.fetchRequest()
                fetchRequest.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? context.fetch(fetchRequest).first {
                    existing.update(from: item)
                } else {
                    let entity = OrderEntity(context: context)
                    entity.update(from: item)
                }
            }
            try? context.save()
        }
    }

    private func importSamples(_ items: [SampleResponseStruct]) {
        let context = self.context
        context.performAndWait {
            for item in items {
                let fetchRequest = SampleEntity.fetchRequest()
                fetchRequest.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? context.fetch(fetchRequest).first {
                    existing.update(from: item)
                } else {
                    let entity = SampleEntity(context: context)
                    entity.update(from: item)
                }
            }
            try? context.save()
        }
    }

    private func importResults(_ items: [TestResultRead]) {
        let context = self.context
        context.performAndWait {
            for item in items {
                let fetchRequest = ResultEntity.fetchRequest()
                fetchRequest.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? context.fetch(fetchRequest).first {
                    existing.update(from: item)
                } else {
                    let entity = ResultEntity(context: context)
                    entity.update(from: item)
                }
            }
            try? context.save()
        }
    }

    private func importNotifications(_ items: [NotificationRecordStruct]) {
        let context = self.context
        context.performAndWait {
            for item in items {
                let fetchRequest = NotificationEntity.fetchRequest()
                fetchRequest.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? context.fetch(fetchRequest).first {
                    existing.update(from: item)
                } else {
                    let entity = NotificationEntity(context: context)
                    entity.update(from: item)
                }
            }
            try? context.save()
        }
    }
}

extension Notification.Name {
    static let syncRequested = Notification.Name("syncRequested")
    static let syncCompleted = Notification.Name("syncCompleted")
}

struct PatientListResponse: Decodable {
    let items: [PatientResponse]
    let pagination: PaginationMetaResponse
}

struct OrderListResponse: Decodable {
    let items: [OrderResponse]
    let pagination: PaginationMetaResponse
}

struct SampleListResponse: Decodable {
    let items: [SampleResponseStruct]
    let pagination: PaginationMetaResponse
}

struct ResultListResponse: Decodable {
    let items: [TestResultRead]
    let pagination: PaginationMetaResponse
}

struct NotificationListResponse: Decodable {
    let items: [NotificationRecordStruct]
    let pagination: PaginationMetaResponse
}

struct PaginationMetaResponse: Decodable {
    let total: Int
    let page: Int
    let limit: Int
    let pages: Int
    let hasNext: Bool
    let hasPrev: Bool
}

struct PatientResponse: Decodable {
    let id: Int
    let fullName: String
    let phone: String
    let birthDate: String?
    let gender: String?
    let email: String?
    let labId: Int
    let status: String
    let createdAt: String
    let updatedAt: String
}

struct OrderResponse: Decodable {
    let id: Int
    let patientId: Int
    let labId: Int
    let doctorName: String?
    let status: String
    let createdAt: String
    let updatedAt: String
    let results: [ResultItemResponseData]
}

struct ResultItemResponseData: Decodable {
    let id: Int
    let orderId: Int
    let testName: String
    let value: Double?
    let valueText: String?
    let unit: String?
    let normalRangeLow: Double?
    let normalRangeHigh: Double?
    let status: String
    let isCritical: Bool
    let isAbnormal: Bool
    let createdAt: String
}

struct SampleResponseStruct: Decodable {
    let id: Int
    let barcode: String
    let orderId: Int
    let sampleType: String
    let status: String
    let collectedBy: String?
    let rejectionReason: String?
    let notes: String?
    let storageLocation: String?
    let collectedAt: String
    let updatedAt: String
}

struct TestResultRead: Decodable {
    let id: Int
    let citizenId: Int
    let labId: Int
    let deviceId: Int?
    let testCode: String
    let testNameEn: String
    let testNameAr: String
    let category: String?
    let resultValue: Double?
    let resultText: String?
    let unit: String?
    let referenceMin: Double?
    let referenceMax: Double?
    let status: String
    let isCritical: Bool
    let isAbnormal: Bool
    let abnormalityDirection: String?
    let sampleCollectedAt: String
    let resultCompletedAt: String?
    let verifiedAt: String?
    let verifiedBy: String?
    let sampleBarcode: String
    let orderingPhysician: String?
    let clinicalNotes: String?
    let createdAt: String
    let updatedAt: String
}

struct NotificationRecordStruct: Decodable {
    let id: Int
    let userId: Int
    let title: String
    let body: String
    let type: String
    let read: Bool
    let createdAt: String
}
