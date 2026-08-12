import Foundation
import CoreData

extension UserEntity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<UserEntity> {
        return NSFetchRequest<UserEntity>(entityName: "UserEntity")
    }

    @NSManaged public var id: Int64
    @NSManaged public var email: String
    @NSManaged public var name: String
    @NSManaged public var role: String
    @NSManaged public var labId: Int64
    @NSManaged public var isActive: Bool
    @NSManaged public var phone: String?
    @NSManaged public var profileImageUrl: String?
    @NSManaged public var lastLoginAt: Date?
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var syncStatus: String?
}
