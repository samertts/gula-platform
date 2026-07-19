import Foundation
import CoreData
import Combine

class ResultRepository: ObservableObject {
    static let shared = ResultRepository()

    @Published var results: [ResultEntity] = []
    @Published var criticalResults: [ResultEntity] = []

    private let context = CoreDataStack.shared.viewContext
    private let backgroundContext = CoreDataStack.shared.backgroundContext

    private init() {
        fetchLocalResults()
        fetchCriticalResults()
    }

    func fetchLocalResults(patientId: Int? = nil, status: String? = nil) {
        let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \ResultEntity.createdAt, ascending: false)]

        var predicates: [NSPredicate] = []
        if let patientId = patientId {
            predicates.append(NSPredicate(format: "citizenId == %d", patientId))
        }
        if let status = status {
            predicates.append(NSPredicate(format: "status == %@", status))
        }
        if !predicates.isEmpty {
            request.predicate = NSCompoundPredicate(andPredicateWithSubpredicates: predicates)
        }

        request.fetchBatchSize = 50

        do {
            let results = try context.fetch(request)
            DispatchQueue.main.async {
                self.results = results
            }
        } catch {
            print("[GULA] Result fetch error: \(error.localizedDescription)")
        }
    }

    func fetchCriticalResults() {
        let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isCritical == YES AND status != %@", "verified")
        request.sortDescriptors = [NSSortDescriptor(keyPath: \ResultEntity.createdAt, ascending: false)]
        request.fetchLimit = 50

        do {
            let results = try context.fetch(request)
            DispatchQueue.main.async {
                self.criticalResults = results
            }
        } catch {
            print("[GULA] Critical result fetch error: \(error.localizedDescription)")
        }
    }

    func getResult(id: Int) -> ResultEntity? {
        let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
        request.predicate = NSPredicate(format: "id == %d", id)
        request.fetchLimit = 1
        return try? context.fetch(request).first
    }

    func refreshFromRemote() async throws {
        let response: ResultListResponse = try await APIClient.shared.request(
            .listResults(page: 1, limit: 200, patientId: nil, status: nil, isCritical: nil)
        )

        backgroundContext.performAndWait {
            for item in response.items {
                let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
                request.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? backgroundContext.fetch(request).first {
                    existing.update(from: item)
                } else {
                    let entity = ResultEntity(context: backgroundContext)
                    entity.update(from: item)
                }
            }
            try? backgroundContext.save()
        }
        fetchLocalResults()
        fetchCriticalResults()
    }

    func verifyResult(id: Int) async throws -> TestResultRead {
        let response: TestResultRead = try await APIClient.shared.request(.verifyResult(id: id))

        backgroundContext.performAndWait {
            let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                entity.status = "verified"
                entity.verifiedAt = Date()
                try? backgroundContext.save()
            }
        }
        fetchLocalResults()
        fetchCriticalResults()
        return response
    }

    func validateResult(id: Int, notes: String?, signatureHash: String?) async throws -> TestResultRead {
        var body: [String: Any] = [:]
        if let notes = notes { body["notes"] = notes }
        if let signatureHash = signatureHash { body["signature_hash"] = signatureHash }
        let response: TestResultRead = try await APIClient.shared.request(
            .validateResult(id: id), body: body
        )

        backgroundContext.performAndWait {
            let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                entity.status = response.status
                if let verifiedAt = response.verifiedAt {
                    entity.verifiedAt = ISO8601DateFormatter().date(from: verifiedAt)
                }
                entity.verifiedBy = response.verifiedBy
                try? backgroundContext.save()
            }
        }
        fetchLocalResults()
        fetchCriticalResults()
        return response
    }

    func flagCritical(id: Int) async throws -> TestResultRead {
        let response: TestResultRead = try await APIClient.shared.request(.flagCritical(id: id))

        backgroundContext.performAndWait {
            let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                entity.isCritical = true
                entity.status = response.status
                try? backgroundContext.save()
            }
        }
        fetchLocalResults()
        fetchCriticalResults()
        return response
    }

    func createResult(data: TestResultCreateInput) async throws -> TestResultRead {
        let body: [String: Any] = [
            "citizen_id": data.citizenId,
            "lab_id": data.labId,
            "test_code": data.testCode,
            "test_name_en": data.testNameEn,
            "test_name_ar": data.testNameAr,
            "result_value": data.resultValue as Any,
            "result_text": data.resultText as Any,
            "unit": data.unit as Any,
            "reference_min": data.referenceMin as Any,
            "reference_max": data.referenceMax as Any,
            "status": data.status,
            "is_critical": data.isCritical,
            "is_abnormal": data.isAbnormal,
            "sample_barcode": data.sampleBarcode,
            "ordering_physician": data.orderingPhysician as Any,
            "clinical_notes": data.clinicalNotes as Any
        ]

        let response: TestResultRead = try await APIClient.shared.request(.createResult, body: body)

        backgroundContext.performAndWait {
            let entity = ResultEntity(context: backgroundContext)
            entity.update(from: response)
            try? backgroundContext.save()
        }
        fetchLocalResults()
        return response
    }

    var criticalCount: Int {
        let request: NSFetchRequest<NSNumber> = ResultEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isCritical == YES")
        request.resultType = .countResultType
        return (try? context.fetch(request).first?.intValue) ?? 0
    }

    var pendingCount: Int {
        let request: NSFetchRequest<NSNumber> = ResultEntity.fetchRequest()
        request.predicate = NSPredicate(format: "status == %@", "pending")
        request.resultType = .countResultType
        return (try? context.fetch(request).first?.intValue) ?? 0
    }
}

struct TestResultCreateInput {
    let citizenId: Int
    let labId: Int
    let testCode: String
    let testNameEn: String
    let testNameAr: String
    let resultValue: Double?
    let resultText: String?
    let unit: String?
    let referenceMin: Double?
    let referenceMax: Double?
    let status: String
    let isCritical: Bool
    let isAbnormal: Bool
    let sampleBarcode: String
    let orderingPhysician: String?
    let clinicalNotes: String?
}
