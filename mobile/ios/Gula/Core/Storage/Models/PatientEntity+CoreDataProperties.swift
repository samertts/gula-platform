import Foundation
import CoreData

extension PatientEntity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<PatientEntity> {
        return NSFetchRequest<PatientEntity>(entityName: "PatientEntity")
    }

    @NSManaged public var id: Int64
    @NSManaged public var fullName: String
    @NSManaged public var phone: String
    @NSManaged public var birthDate: String?
    @NSManaged public var gender: String?
    @NSManaged public var email: String?
    @NSManaged public var labId: Int64
    @NSManaged public var status: String
    @NSManaged public var nationalId: String?
    @NSManaged public var familyId: String?
    @NSManaged public var guardianId: Int64
    @NSManaged public var citizenUlid: String?
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var version: Int64
    @NSManaged public var syncStatus: String?
    @NSManaged public var searchName: String?

    func update(from response: PatientResponse) {
        self.id = Int64(response.id)
        self.fullName = response.fullName
        self.phone = response.phone
        self.birthDate = response.birthDate
        self.gender = response.gender
        self.email = response.email
        self.labId = Int64(response.labId)
        self.status = response.status

        let dateFormatter = ISO8601DateFormatter()
        if let createdAt = response.createdAt {
            self.createdAt = dateFormatter.date(from: createdAt)
        }
        if let updatedAt = response.updatedAt {
            self.updatedAt = dateFormatter.date(from: updatedAt)
        }

        self.searchName = response.fullName.lowercased()
            .applyingTransform(.stripDiacritics, reverse: false)?
            .applyingTransform(.stripCombiningMarks, reverse: false) ?? response.fullName.lowercased()
    }
}
