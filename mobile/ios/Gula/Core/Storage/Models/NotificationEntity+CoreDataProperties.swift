import Foundation
import CoreData

extension NotificationEntity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<NotificationEntity> {
        return NSFetchRequest<NotificationEntity>(entityName: "NotificationEntity")
    }

    @NSManaged public var id: Int64
    @NSManaged public var userId: Int64
    @NSManaged public var title: String
    @NSManaged public var bodyStr: String
    @NSManaged public var typeStr: String
    @NSManaged public var read: Bool
    @NSManaged public var dataPayload: Data?
    @NSManaged public var createdAt: Date?
    @NSManaged public var syncStatus: String?

    func update(from response: NotificationRecordStruct) {
        self.id = Int64(response.id)
        self.userId = Int64(response.userId)
        self.title = response.title
        self.bodyStr = response.body
        self.typeStr = response.type
        self.read = response.read

        let dateFormatter = ISO8601DateFormatter()
        if let createdAt = response.createdAt {
            self.createdAt = dateFormatter.date(from: createdAt)
        }
    }
}
