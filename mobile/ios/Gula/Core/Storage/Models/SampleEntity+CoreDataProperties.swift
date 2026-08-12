import Foundation
import CoreData

extension SampleEntity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<SampleEntity> {
        return NSFetchRequest<SampleEntity>(entityName: "SampleEntity")
    }

    @NSManaged public var id: Int64
    @NSManaged public var barcode: String
    @NSManaged public var orderId: Int64
    @NSManaged public var sampleType: String
    @NSManaged public var status: String
    @NSManaged public var collectedBy: String?
    @NSManaged public var rejectionReason: String?
    @NSManaged public var notes: String?
    @NSManaged public var storageLocation: String?
    @NSManaged public var collectedAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var version: Int64
    @NSManaged public var syncStatus: String?
    @NSManaged public var order: OrderEntity?

    func update(from response: SampleResponseStruct) {
        self.id = Int64(response.id)
        self.barcode = response.barcode
        self.orderId = Int64(response.orderId)
        self.sampleType = response.sampleType
        self.status = response.status
        self.collectedBy = response.collectedBy
        self.rejectionReason = response.rejectionReason
        self.notes = response.notes
        self.storageLocation = response.storageLocation

        let dateFormatter = ISO8601DateFormatter()
        if let collectedAt = response.collectedAt {
            self.collectedAt = dateFormatter.date(from: collectedAt)
        }
        if let updatedAt = response.updatedAt {
            self.updatedAt = dateFormatter.date(from: updatedAt)
        }
    }
}
