import Foundation
import CoreData

extension SyncQueueItemEntity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<SyncQueueItemEntity> {
        return NSFetchRequest<SyncQueueItemEntity>(entityName: "SyncQueueItemEntity")
    }

    @NSManaged public var id: String
    @NSManaged public var operationType: String
    @NSManaged public var entityType: String?
    @NSManaged public var entityId: String?
    @NSManaged public var endpointPath: String
    @NSManaged public var httpMethod: String
    @NSManaged public var requestBody: Data?
    @NSManaged public var createdAt: Date?
    @NSManaged public var retryCount: Int64
    @NSManaged public var maxRetries: Int64
    @NSManaged public var status: String
    @NSManaged public var lastError: String?
    @NSManaged public var priority: Int64
}
