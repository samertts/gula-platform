import Foundation
import CoreData

struct SyncOperation: Identifiable, Codable, Equatable {
    let id: String
    let type: SyncOperationType
    let endpoint: APIEndpoint
    let body: Data?
    let createdAt: Date
    var retryCount: Int
    let maxRetries: Int
    var status: SyncOperationStatus
    var lastError: String?
    let idempotencyKey: String
    let priority: SyncPriority

    init(
        type: SyncOperationType,
        endpoint: APIEndpoint,
        body: Encodable? = nil,
        retryCount: Int = 0,
        maxRetries: Int = 5,
        priority: SyncPriority = .normal
    ) {
        self.id = UUID().uuidString
        self.type = type
        self.endpoint = endpoint
        self.body = body.flatMap { try? JSONEncoder().encode(AnyEncodable($0)) }
        self.createdAt = Date()
        self.retryCount = retryCount
        self.maxRetries = maxRetries
        self.status = .pending
        self.lastError = nil
        self.idempotencyKey = UUID().uuidString
        self.priority = priority
    }
}

enum SyncOperationType: String, Codable {
    case create, update, delete
}

enum SyncOperationStatus: String, Codable {
    case pending, processing, completed, failed, conflict
}

enum SyncPriority: Int, Codable, Comparable {
    case low = 0
    case normal = 1
    case high = 2
    case critical = 3

    static func < (lhs: SyncPriority, rhs: SyncPriority) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}

class SyncQueue: ObservableObject {
    static let shared = SyncQueue()

    @Published var operations: [SyncOperation] = []
    @Published var pendingCount: Int = 0
    @Published var failedCount: Int = 0

    private let queue: OperationQueue
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private var saveTimer: Timer?

    private var storageURL: URL {
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return documents.appendingPathComponent("sync_queue.json")
    }

    private init() {
        queue = OperationQueue()
        queue.maxConcurrentOperationCount = 1
        queue.qualityOfService = .utility

        encoder.outputFormatting = .prettyPrinted
        loadFromDisk()

        saveTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.saveToDisk()
        }
    }

    func enqueue(_ operation: SyncOperation) {
        DispatchQueue.main.async {
            self.operations.append(operation)
            self.operations.sort { $0.priority > $1.priority || ($0.priority == $1.priority && $0.createdAt < $1.createdAt) }
            self.updateCounts()
            self.saveToDisk()
        }
    }

    func enqueueHighPriority(_ operation: SyncOperation) {
        var highPriority = operation
        highPriority = SyncOperation(
            type: operation.type,
            endpoint: operation.endpoint,
            body: operation.body.flatMap { try? JSONSerialization.jsonObject(with: $0) as? Encodable },
            retryCount: operation.retryCount,
            maxRetries: operation.maxRetries,
            priority: .high
        )
        enqueue(highPriority)
    }

    func dequeue(id: String) {
        DispatchQueue.main.async {
            self.operations.removeAll { $0.id == id }
            self.updateCounts()
            self.saveToDisk()
        }
    }

    func markFailed(id: String, error: String) {
        DispatchQueue.main.async {
            if let index = self.operations.firstIndex(where: { $0.id == id }) {
                var op = self.operations[index]
                op.retryCount += 1
                op.lastError = error
                op.status = op.retryCount >= op.maxRetries ? .failed : .pending
                self.operations[index] = op
                self.updateCounts()
                self.saveToDisk()
            }
        }
    }

    func markCompleted(id: String) {
        DispatchQueue.main.async {
            if let index = self.operations.firstIndex(where: { $0.id == id }) {
                var op = self.operations[index]
                op.status = .completed
                self.operations[index] = op
            }
            self.operations.removeAll { $0.id == id }
            self.updateCounts()
            self.saveToDisk()
        }
    }

    func markConflict(id: String, error: String) {
        DispatchQueue.main.async {
            if let index = self.operations.firstIndex(where: { $0.id == id }) {
                var op = self.operations[index]
                op.status = .conflict
                op.lastError = error
                self.operations[index] = op
                self.updateCounts()
                self.saveToDisk()
            }
        }
    }

    func nextPending() -> SyncOperation? {
        operations
            .filter { $0.status == .pending }
            .sorted { $0.priority > $1.priority || ($0.priority == $1.priority && $0.createdAt < $1.createdAt) }
            .first
    }

    func clearCompleted() {
        DispatchQueue.main.async {
            self.operations.removeAll { $0.status == .completed }
            self.updateCounts()
            self.saveToDisk()
        }
    }

    func clearAll() {
        DispatchQueue.main.async {
            self.operations.removeAll()
            self.updateCounts()
            self.saveToDisk()
        }
    }

    func clearFailed() {
        DispatchQueue.main.async {
            self.operations.removeAll { $0.status == .failed }
            self.updateCounts()
            self.saveToDisk()
        }
    }

    func retryFailed() {
        DispatchQueue.main.async {
            for i in self.operations.indices where self.operations[i].status == .failed {
                var op = self.operations[i]
                op.status = .pending
                op.retryCount = 0
                self.operations[i] = op
            }
            self.updateCounts()
            self.saveToDisk()
        }
    }

    var hasPending: Bool {
        operations.contains { $0.status == .pending }
    }

    var hasFailed: Bool {
        operations.contains { $0.status == .failed }
    }

    private func updateCounts() {
        pendingCount = operations.filter { $0.status == .pending || $0.status == .processing }.count
        failedCount = operations.filter { $0.status == .failed }.count
    }

    private func saveToDisk() {
        guard let data = try? encoder.encode(operations) else { return }
        try? data.write(to: storageURL, options: .atomic)
    }

    private func loadFromDisk() {
        guard let data = try? Data(contentsOf: storageURL),
              let ops = try? decoder.decode([SyncOperation].self, from: data) else { return }
        DispatchQueue.main.async {
            self.operations = ops.filter { $0.status != .completed }
            self.updateCounts()
        }
    }
}
