import XCTest
@testable import Gula

final class SyncEngineTests: XCTestCase {
    var sut: SyncEngine!
    var queue: SyncQueue!

    override func setUp() {
        super.setUp()
        sut = SyncEngine.shared
        queue = SyncQueue.shared
        queue.clearAll()
    }

    override func tearDown() {
        queue.clearAll()
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertFalse(sut.isSyncing)
        XCTAssertEqual(queue.operations.count, 0)
        XCTAssertEqual(queue.pendingCount, 0)
    }

    func testEnqueueOperation() {
        let operation = SyncOperation(
            type: .create,
            endpoint: .createPatient,
            body: ["full_name": "Test Patient", "phone": "+964770000000"],
            maxRetries: 3,
            priority: .high
        )

        queue.enqueue(operation)

        XCTAssertEqual(queue.operations.count, 1)
        XCTAssertEqual(queue.pendingCount, 1)
        XCTAssertEqual(queue.operations.first?.id, operation.id)
    }

    func testEnqueueMultipleOperations() {
        let op1 = SyncOperation(type: .create, endpoint: .createPatient, maxRetries: 3)
        let op2 = SyncOperation(type: .update, endpoint: .updatePatient(id: 1), maxRetries: 3)
        let op3 = SyncOperation(type: .delete, endpoint: .deletePatient(id: 1), maxRetries: 3)

        queue.enqueue(op1)
        queue.enqueue(op2)
        queue.enqueue(op3)

        XCTAssertEqual(queue.operations.count, 3)
        XCTAssertEqual(queue.pendingCount, 3)
    }

    func testDequeueOperation() {
        let operation = SyncOperation(type: .create, endpoint: .createPatient)
        queue.enqueue(operation)

        queue.dequeue(id: operation.id)

        XCTAssertEqual(queue.operations.count, 0)
        XCTAssertEqual(queue.pendingCount, 0)
    }

    func testMarkFailed() {
        let operation = SyncOperation(type: .create, endpoint: .createPatient, maxRetries: 2)
        queue.enqueue(operation)

        queue.markFailed(id: operation.id, error: "Network error")
        queue.markFailed(id: operation.id, error: "Network error")

        XCTAssertTrue(queue.hasFailed)
        XCTAssertEqual(queue.failedCount, 1)
    }

    func testMarkCompleted() {
        let operation = SyncOperation(type: .create, endpoint: .createPatient)
        queue.enqueue(operation)

        queue.markCompleted(id: operation.id)

        XCTAssertEqual(queue.operations.count, 0)
    }

    func testRetryFailed() {
        let operation = SyncOperation(type: .create, endpoint: .createPatient, maxRetries: 1)
        queue.enqueue(operation)

        queue.markFailed(id: operation.id, error: "Error")
        queue.retryFailed()

        XCTAssertEqual(queue.pendingCount, 1)
        XCTAssertEqual(queue.failedCount, 0)
    }

    func testClearFailed() {
        let operation = SyncOperation(type: .create, endpoint: .createPatient, maxRetries: 1)
        queue.enqueue(operation)
        queue.markFailed(id: operation.id, error: "Error")

        queue.clearFailed()

        XCTAssertEqual(queue.operations.count, 0)
    }

    func testPriorityOrdering() {
        let low = SyncOperation(type: .create, endpoint: .createPatient, priority: .low)
        let high = SyncOperation(type: .create, endpoint: .createPatient, priority: .high)

        queue.enqueue(low)
        queue.enqueue(high)

        let next = queue.nextPending()
        XCTAssertEqual(next?.priority, SyncPriority.high)
    }

    func testSyncOperationEquality() {
        let op1 = SyncOperation(type: .create, endpoint: .createPatient)
        let op2 = SyncOperation(type: .create, endpoint: .createPatient)
        XCTAssertNotEqual(op1, op2)
        XCTAssertEqual(op1.id == op2.id, false)
    }

    func testSyncOperationEncodeDecode() throws {
        let operation = SyncOperation(
            type: .update,
            endpoint: .updatePatient(id: 10),
            body: ["name": "Test"],
            maxRetries: 3,
            priority: .normal
        )

        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        let data = try encoder.encode(operation)
        let decoded = try decoder.decode(SyncOperation.self, from: data)

        XCTAssertEqual(decoded.id, operation.id)
        XCTAssertEqual(decoded.type, operation.type)
        XCTAssertEqual(decoded.maxRetries, operation.maxRetries)
        XCTAssertEqual(decoded.priority, operation.priority)
    }

    func testSyncPriorityComparable() {
        XCTAssertTrue(SyncPriority.low < SyncPriority.normal)
        XCTAssertTrue(SyncPriority.normal < SyncPriority.high)
        XCTAssertTrue(SyncPriority.high < SyncPriority.critical)
        XCTAssertEqual(SyncPriority.normal, SyncPriority.normal)
    }
}
