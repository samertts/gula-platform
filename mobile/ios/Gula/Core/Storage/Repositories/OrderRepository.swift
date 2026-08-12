import Foundation
import CoreData
import Combine

class OrderRepository: ObservableObject {
    static let shared = OrderRepository()

    @Published var orders: [OrderEntity] = []

    private let context = CoreDataStack.shared.viewContext
    private let backgroundContext = CoreDataStack.shared.backgroundContext

    private init() {
        fetchLocalOrders()
    }

    func fetchLocalOrders(status: String? = nil, patientId: Int? = nil) {
        let request: NSFetchRequest<OrderEntity> = OrderEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \OrderEntity.createdAt, ascending: false)]

        var predicates: [NSPredicate] = []
        if let status = status {
            predicates.append(NSPredicate(format: "status == %@", status))
        }
        if let patientId = patientId {
            predicates.append(NSPredicate(format: "patientId == %d", patientId))
        }
        if !predicates.isEmpty {
            request.predicate = NSCompoundPredicate(andPredicateWithSubpredicates: predicates)
        }

        request.fetchBatchSize = 50

        do {
            let results = try context.fetch(request)
            DispatchQueue.main.async {
                self.orders = results
            }
        } catch {
            print("[GULA] Order fetch error: \(error.localizedDescription)")
        }
    }

    func getOrder(id: Int) -> OrderEntity? {
        let request: NSFetchRequest<OrderEntity> = OrderEntity.fetchRequest()
        request.predicate = NSPredicate(format: "id == %d", id)
        request.fetchLimit = 1
        return try? context.fetch(request).first
    }

    func refreshFromRemote() async throws {
        let response: OrderListResponse = try await APIClient.shared.request(
            .listOrders(page: 1, limit: 200, patientId: nil, status: nil)
        )

        backgroundContext.performAndWait {
            for item in response.items {
                let request: NSFetchRequest<OrderEntity> = OrderEntity.fetchRequest()
                request.predicate = NSPredicate(format: "id == %d", item.id)
                if let existing = try? backgroundContext.fetch(request).first {
                    existing.update(from: item)
                } else {
                    let entity = OrderEntity(context: backgroundContext)
                    entity.update(from: item)
                }
            }
            try? backgroundContext.save()
        }
        fetchLocalOrders()
    }

    func createOrder(patientId: Int, doctorName: String?, results: [ResultItemData]) async throws -> OrderResponse {
        let body: [String: Any] = [
            "patient_id": patientId,
            "doctor_name": doctorName as Any,
            "results": results.map { r in
                [
                    "test_name": r.testName,
                    "value": r.value as Any,
                    "value_text": r.valueText as Any,
                    "unit": r.unit as Any,
                    "normal_range_low": r.normalRangeLow as Any,
                    "normal_range_high": r.normalRangeHigh as Any
                ]
            }
        ]

        let response: OrderResponse = try await APIClient.shared.request(.createOrder, body: body)

        backgroundContext.performAndWait {
            let entity = OrderEntity(context: backgroundContext)
            entity.update(from: response)
            try? backgroundContext.save()
        }
        fetchLocalOrders()
        return response
    }

    func cancelOrder(id: Int) async throws -> OrderResponse {
        let response: OrderResponse = try await APIClient.shared.request(.cancelOrder(id: id))
        backgroundContext.performAndWait {
            if let entity = try? backgroundContext.fetch(
                OrderEntity.fetchRequest().applying { $0.predicate = NSPredicate(format: "id == %d", id) }
            ).first {
                entity.status = "cancelled"
                try? backgroundContext.save()
            }
        }
        fetchLocalOrders()
        return response
    }

    var pendingCount: Int {
        let request: NSFetchRequest<NSNumber> = OrderEntity.fetchRequest()
        request.predicate = NSPredicate(format: "status != %@ AND status != %@", "completed", "cancelled")
        request.resultType = .countResultType
        return (try? context.fetch(request).first?.intValue) ?? 0
    }

    var todayCount: Int {
        let request: NSFetchRequest<NSNumber> = OrderEntity.fetchRequest()
        let cal = Calendar.current
        let startOfDay = cal.startOfDay(for: Date())
        request.predicate = NSPredicate(format: "createdAt >= %@", startOfDay as NSDate)
        request.resultType = .countResultType
        return (try? context.fetch(request).first?.intValue) ?? 0
    }
}

struct ResultItemData: Encodable {
    let testName: String
    let value: Double?
    let valueText: String?
    let unit: String?
    let normalRangeLow: Double?
    let normalRangeHigh: Double?

    enum CodingKeys: String, CodingKey {
        case testName = "test_name"
        case value, valueText = "value_text", unit
        case normalRangeLow = "normal_range_low"
        case normalRangeHigh = "normal_range_high"
    }
}

extension NSFetchRequest {
    func applying(_ block: (NSFetchRequest) -> Void) -> Self {
        block(self)
        return self
    }
}
