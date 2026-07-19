import Foundation
import CoreData

extension ResultEntity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<ResultEntity> {
        return NSFetchRequest<ResultEntity>(entityName: "ResultEntity")
    }

    @NSManaged public var id: Int64
    @NSManaged public var citizenId: Int64
    @NSManaged public var labId: Int64
    @NSManaged public var deviceId: Int64
    @NSManaged public var testCode: String
    @NSManaged public var testNameEn: String
    @NSManaged public var testNameAr: String
    @NSManaged public var category: String?
    @NSManaged public var resultValue: Double
    @NSManaged public var resultText: String?
    @NSManaged public var unit: String?
    @NSManaged public var referenceMin: Double
    @NSManaged public var referenceMax: Double
    @NSManaged public var status: String
    @NSManaged public var isCritical: Bool
    @NSManaged public var isAbnormal: Bool
    @NSManaged public var abnormalityDirection: String?
    @NSManaged public var sampleCollectedAt: Date?
    @NSManaged public var resultCompletedAt: Date?
    @NSManaged public var verifiedAt: Date?
    @NSManaged public var verifiedBy: String?
    @NSManaged public var sampleBarcode: String
    @NSManaged public var orderingPhysician: String?
    @NSManaged public var clinicalNotes: String?
    @NSManaged public var orderId: Int64
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var version: Int64
    @NSManaged public var syncStatus: String?
    @NSManaged public var order: OrderEntity?

    func update(from response: TestResultRead) {
        self.id = Int64(response.id)
        self.citizenId = Int64(response.citizenId)
        self.labId = Int64(response.labId)
        if let deviceId = response.deviceId { self.deviceId = Int64(deviceId) }
        self.testCode = response.testCode
        self.testNameEn = response.testNameEn
        self.testNameAr = response.testNameAr
        self.category = response.category
        if let value = response.resultValue { self.resultValue = value }
        self.resultText = response.resultText
        self.unit = response.unit
        if let min = response.referenceMin { self.referenceMin = min }
        if let max = response.referenceMax { self.referenceMax = max }
        self.status = response.status
        self.isCritical = response.isCritical
        self.isAbnormal = response.isAbnormal
        self.abnormalityDirection = response.abnormalityDirection

        let dateFormatter = ISO8601DateFormatter()
        if let collectedAt = response.sampleCollectedAt {
            self.sampleCollectedAt = dateFormatter.date(from: collectedAt)
        }
        if let completedAt = response.resultCompletedAt {
            self.resultCompletedAt = dateFormatter.date(from: completedAt)
        }
        if let verifiedAt = response.verifiedAt {
            self.verifiedAt = dateFormatter.date(from: verifiedAt)
        }
        self.verifiedBy = response.verifiedBy
        self.sampleBarcode = response.sampleBarcode
        self.orderingPhysician = response.orderingPhysician
        self.clinicalNotes = response.clinicalNotes
        if let createdAt = response.createdAt {
            self.createdAt = dateFormatter.date(from: createdAt)
        }
        if let updatedAt = response.updatedAt {
            self.updatedAt = dateFormatter.date(from: updatedAt)
        }
    }
}
