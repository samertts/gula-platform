import Foundation
import CoreData

extension OrderEntity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<OrderEntity> {
        return NSFetchRequest<OrderEntity>(entityName: "OrderEntity")
    }

    @NSManaged public var id: Int64
    @NSManaged public var patientId: Int64
    @NSManaged public var labId: Int64
    @NSManaged public var doctorName: String?
    @NSManaged public var doctorUserId: Int64
    @NSManaged public var status: String
    @NSManaged public var priority: String?
    @NSManaged public var notes: String?
    @NSManaged public var visitId: Int64
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var version: Int64
    @NSManaged public var syncStatus: String?
    @NSManaged public var patient: PatientEntity?
    @NSManaged public var results: Set<ResultEntity>?

    func update(from response: OrderResponse) {
        self.id = Int64(response.id)
        self.patientId = Int64(response.patientId)
        self.labId = Int64(response.labId)
        self.doctorName = response.doctorName
        self.status = response.status

        let dateFormatter = ISO8601DateFormatter()
        if let createdAt = response.createdAt {
            self.createdAt = dateFormatter.date(from: createdAt)
        }
        if let updatedAt = response.updatedAt {
            self.updatedAt = dateFormatter.date(from: updatedAt)
        }
    }
}
