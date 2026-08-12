import Foundation
import CoreData
import Combine

class PatientRepository: ObservableObject {
    static let shared = PatientRepository()

    @Published var patients: [PatientEntity] = []

    private let context = CoreDataStack.shared.viewContext
    private let backgroundContext = CoreDataStack.shared.backgroundContext

    private init() {
        fetchLocalPatients()
    }

    func fetchLocalPatients(search: String? = nil, labId: Int? = nil) {
        let request: NSFetchRequest<PatientEntity> = PatientEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \PatientEntity.fullName, ascending: true)]

        var predicates: [NSPredicate] = []
        if let search = search, !search.isEmpty {
            predicates.append(NSPredicate(format: "searchName CONTAINS[cd] %@ OR phone CONTAINS[cd] %@", search, search))
        }
        if let labId = labId {
            predicates.append(NSPredicate(format: "labId == %d", labId))
        }
        if !predicates.isEmpty {
            request.predicate = NSCompoundPredicate(andPredicateWithSubpredicates: predicates)
        }

        request.fetchBatchSize = 50

        do {
            let results = try context.fetch(request)
            DispatchQueue.main.async {
                self.patients = results
            }
        } catch {
            print("[GULA] Patient fetch error: \(error.localizedDescription)")
        }
    }

    func getPatient(id: Int) -> PatientEntity? {
        let request: NSFetchRequest<PatientEntity> = PatientEntity.fetchRequest()
        request.predicate = NSPredicate(format: "id == %d", id)
        request.fetchLimit = 1
        return try? context.fetch(request).first
    }

    func refreshFromRemote() async throws {
        let response: PatientListResponse = try await APIClient.shared.request(
            .listPatients(page: 1, limit: 200, search: nil, gender: nil, status: nil)
        )

        backgroundContext.performAndWait {
            for item in response.items {
                let request: NSFetchRequest<PatientEntity> = PatientEntity.fetchRequest()
                request.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? backgroundContext.fetch(request).first {
                    existing.update(from: item)
                } else {
                    let entity = PatientEntity(context: backgroundContext)
                    entity.update(from: item)
                }
            }
            try? backgroundContext.save()
        }

        fetchLocalPatients()
    }

    func savePatient(patient: PatientResponse) {
        backgroundContext.performAndWait {
            let request: NSFetchRequest<PatientEntity> = PatientEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", patient.id)
            if let existing = try? backgroundContext.fetch(request).first {
                existing.update(from: patient)
            } else {
                let entity = PatientEntity(context: backgroundContext)
                entity.update(from: patient)
            }
            try? backgroundContext.save()
        }
        fetchLocalPatients()
    }

    func getPatientHistory(id: Int) async throws -> PatientHistoryData {
        return try await APIClient.shared.request(.patientHistory(id: id))
    }

    func searchRemote(query: String, page: Int = 1) async throws -> [PatientResponse] {
        let response: PatientListResponse = try await APIClient.shared.request(
            .searchPatients(query: query, page: page, limit: 50)
        )
        return response.items
    }

    func deletePatient(id: Int) async throws {
        try await APIClient.shared.requestVoid(.deletePatient(id: id))
        backgroundContext.performAndWait {
            let request: NSFetchRequest<PatientEntity> = PatientEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                backgroundContext.delete(entity)
                try? backgroundContext.save()
            }
        }
        fetchLocalPatients()
    }

    var patientCount: Int {
        let request: NSFetchRequest<NSNumber> = PatientEntity.fetchRequest()
        request.resultType = .countResultType
        return (try? context.fetch(request).first?.intValue) ?? 0
    }
}

struct PatientHistoryData: Decodable {
    let orders: [OrderResponse]
    let results: [TestResultBriefData]
    let samples: [SampleResponseStruct]
}

struct TestResultBriefData: Decodable {
    let id: Int
    let testCode: String
    let testNameEn: String
    let testNameAr: String
    let resultValue: Double?
    let resultText: String?
    let unit: String?
    let status: String
    let isAbnormal: Bool
    let isCritical: Bool
    let sampleCollectedAt: String
}
