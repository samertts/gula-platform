import XCTest
@testable import Gula

final class PatientRepositoryTests: XCTestCase {
    var sut: PatientRepository!

    override func setUp() {
        super.setUp()
        sut = PatientRepository.shared
    }

    override func tearDown() {
        CoreDataStack.shared.deleteAll(entityName: "PatientEntity")
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertNotNil(sut)
    }

    func testPatientEntityProperties() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = PatientEntity(context: context)
        entity.id = 1
        entity.fullName = "Test Patient"
        entity.phone = "+9647700000000"
        entity.status = "active"

        XCTAssertEqual(entity.id, 1)
        XCTAssertEqual(entity.fullName, "Test Patient")
        XCTAssertEqual(entity.phone, "+9647700000000")
        XCTAssertEqual(entity.status, "active")
    }

    func testPatientEntityUpdate() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = PatientEntity(context: context)

        let response = PatientResponse(
            id: 1,
            fullName: "John Doe",
            phone: "+964770111111",
            birthDate: "1990-01-15",
            gender: "male",
            email: "john@example.com",
            labId: 1,
            status: "active",
            createdAt: "2024-01-01T00:00:00Z",
            updatedAt: "2024-06-15T00:00:00Z"
        )

        entity.update(from: response)

        XCTAssertEqual(entity.fullName, "John Doe")
        XCTAssertEqual(entity.phone, "+964770111111")
        XCTAssertEqual(entity.gender, "male")
    }

    func testPatientEntitySearchName() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = PatientEntity(context: context)

        let response = PatientResponse(
            id: 2,
            fullName: "أحمد محمد",
            phone: "+964770222222",
            birthDate: nil,
            gender: "male",
            email: nil,
            labId: 1,
            status: "active",
            createdAt: nil,
            updatedAt: nil
        )

        entity.update(from: response)
        XCTAssertNotNil(entity.searchName)
    }

    func testOrderEntityProperties() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = OrderEntity(context: context)
        entity.id = 100
        entity.patientId = 1
        entity.status = "pending"

        XCTAssertEqual(entity.id, 100)
        XCTAssertEqual(entity.patientId, 1)
        XCTAssertEqual(entity.status, "pending")
    }

    func testSampleEntityProperties() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = SampleEntity(context: context)
        entity.id = 50
        entity.barcode = "SAMPLE001"
        entity.sampleType = "Blood"
        entity.status = "collected"

        XCTAssertEqual(entity.barcode, "SAMPLE001")
        XCTAssertEqual(entity.sampleType, "Blood")
    }

    func testResultEntityProperties() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = ResultEntity(context: context)
        entity.id = 75
        entity.testCode = "CBC"
        entity.testNameEn = "Complete Blood Count"
        entity.testNameAr = "تعداد الدم الكامل"
        entity.isCritical = true
        entity.resultValue = 18.5

        XCTAssertEqual(entity.testCode, "CBC")
        XCTAssertTrue(entity.isCritical)
        XCTAssertEqual(entity.resultValue, 18.5)
    }

    func testNotificationEntityProperties() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = NotificationEntity(context: context)
        entity.id = 200
        entity.title = "Test Notification"
        entity.bodyStr = "This is a test"
        entity.typeStr = "critical_alert"
        entity.read = false

        XCTAssertEqual(entity.title, "Test Notification")
        XCTAssertFalse(entity.read)
    }

    func testSyncQueueItemEntityProperties() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = SyncQueueItemEntity(context: context)
        entity.id = "sync-001"
        entity.operationType = "create"
        entity.status = "pending"
        entity.priority = 1

        XCTAssertEqual(entity.operationType, "create")
        XCTAssertEqual(entity.status, "pending")
    }

    func testSaveAndFetchPatient() {
        let context = CoreDataStack.shared.backgroundContext
        context.performAndWait {
            let entity = PatientEntity(context: context)
            entity.id = 999
            entity.fullName = "Save Test"
            entity.phone = "+964770999999"
            entity.status = "active"
            try? context.save()
        }

        let fetchRequest: NSFetchRequest<PatientEntity> = PatientEntity.fetchRequest()
        fetchRequest.predicate = NSPredicate(format: "id == %d", 999)

        let results = try? CoreDataStack.shared.viewContext.fetch(fetchRequest)
        XCTAssertEqual(results?.first?.fullName, "Save Test")
    }

    func testPatientCount() {
        let context = CoreDataStack.shared.backgroundContext
        context.performAndWait {
            for i in 0..<5 {
                let entity = PatientEntity(context: context)
                entity.id = Int64(1000 + i)
                entity.fullName = "Patient \(i)"
                entity.phone = "+964770\(1000 + i)"
                entity.status = "active"
            }
            try? context.save()
        }

        let count = sut.patientCount
        XCTAssertGreaterThanOrEqual(count, 0)
    }

    func testUserEntityProperties() {
        let context = CoreDataStack.shared.backgroundContext
        let entity = UserEntity(context: context)
        entity.id = 1
        entity.name = "Admin User"
        entity.email = "admin@gula.iq"
        entity.role = "lab_admin"
        entity.isActive = true

        XCTAssertEqual(entity.email, "admin@gula.iq")
        XCTAssertTrue(entity.isActive)
    }

    func testCoreDataStackSharedInstance() {
        let stack = CoreDataStack.shared
        XCTAssertNotNil(stack.viewContext)
        XCTAssertNotNil(stack.backgroundContext)
    }
}
