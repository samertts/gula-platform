import Foundation
import CoreData
import Combine

class SampleRepository: ObservableObject {
    static let shared = SampleRepository()

    @Published var samples: [SampleEntity] = []

    private let context = CoreDataStack.shared.viewContext
    private let backgroundContext = CoreDataStack.shared.backgroundContext

    private init() {
        fetchLocalSamples()
    }

    func fetchLocalSamples(status: String? = nil) {
        let request: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \SampleEntity.collectedAt, ascending: false)]

        var predicates: [NSPredicate] = []
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
                self.samples = results
            }
        } catch {
            print("[GULA] Sample fetch error: \(error.localizedDescription)")
        }
    }

    func getSample(id: Int) -> SampleEntity? {
        let request: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
        request.predicate = NSPredicate(format: "id == %d", id)
        request.fetchLimit = 1
        return try? context.fetch(request).first
    }

    func lookupByBarcode(barcode: String) -> SampleEntity? {
        let request: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
        request.predicate = NSPredicate(format: "barcode == %@", barcode)
        request.fetchLimit = 1
        return try? context.fetch(request).first
    }

    func refreshFromRemote() async throws {
        let response: SampleListResponse = try await APIClient.shared.request(
            .listSamples(page: 1, limit: 200, status: nil, type: nil)
        )

        backgroundContext.performAndWait {
            for item in response.items {
                let request: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
                request.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? backgroundContext.fetch(request).first {
                    existing.update(from: item)
                } else {
                    let entity = SampleEntity(context: backgroundContext)
                    entity.update(from: item)
                }
            }
            try? backgroundContext.save()
        }
        fetchLocalSamples()
    }

    func createSample(orderId: Int, sampleType: String) async throws -> SampleResponseStruct {
        let body: [String: Any] = [
            "order_id": orderId,
            "sample_type": sampleType
        ]
        let response: SampleResponseStruct = try await APIClient.shared.request(.createSample, body: body)

        backgroundContext.performAndWait {
            let entity = SampleEntity(context: backgroundContext)
            entity.update(from: response)
            try? backgroundContext.save()
        }
        fetchLocalSamples()
        return response
    }

    func receiveSample(id: Int) async throws -> SampleResponseStruct {
        let response: SampleResponseStruct = try await APIClient.shared.request(.receiveSample(id: id))

        backgroundContext.performAndWait {
            let request: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                entity.status = "received"
                try? backgroundContext.save()
            }
        }
        fetchLocalSamples()
        return response
    }

    func rejectSample(id: Int, reason: String) async throws -> SampleResponseStruct {
        let response: SampleResponseStruct = try await APIClient.shared.request(
            .rejectSample(id: id), body: ["reason": reason]
        )

        backgroundContext.performAndWait {
            let request: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", id)
            if let entity = try? backgroundContext.fetch(request).first {
                entity.status = "rejected"
                entity.rejectionReason = reason
                try? backgroundContext.save()
            }
        }
        fetchLocalSamples()
        return response
    }

    func lookupRemoteByBarcode(barcode: String) async throws -> SampleResponseStruct {
        return try await APIClient.shared.request(.lookupSampleByBarcode(barcode: barcode))
    }

    var todayCollectionCount: Int {
        let request: NSFetchRequest<NSNumber> = SampleEntity.fetchRequest()
        let cal = Calendar.current
        let startOfDay = cal.startOfDay(for: Date())
        request.predicate = NSPredicate(format: "collectedAt >= %@", startOfDay as NSDate)
        request.resultType = .countResultType
        return (try? context.fetch(request).first?.intValue) ?? 0
    }
}
