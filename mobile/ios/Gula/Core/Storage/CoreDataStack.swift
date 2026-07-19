import Foundation
import CoreData

class CoreDataStack {
    static let shared = CoreDataStack()

    lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "Gula")
        let description = container.persistentStoreDescriptions.first
        description?.shouldMigrateStoreAutomatically = true
        description?.shouldInferMappingModelAutomatically = true

        let storeURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
            .appendingPathComponent("Gula.sqlite")
        description?.url = storeURL

        container.loadPersistentStores { _, error in
            if let error = error {
                fatalError("CoreData loading error: \(error.localizedDescription)")
            }
        }

        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy

        return container
    }()

    var viewContext: NSManagedObjectContext {
        persistentContainer.viewContext
    }

    var backgroundContext: NSManagedObjectContext {
        let context = persistentContainer.newBackgroundContext()
        context.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        return context
    }

    private init() {}

    func saveContext() {
        let context = persistentContainer.viewContext
        guard context.hasChanges else { return }
        do {
            try context.save()
        } catch {
            print("[GULA] CoreData save error: \(error.localizedDescription)")
        }
    }

    func saveBackgroundContext(_ context: NSManagedObjectContext) {
        context.performAndWait {
            guard context.hasChanges else { return }
            do {
                try context.save()
            } catch {
                print("[GULA] CoreData background save error: \(error.localizedDescription)")
            }
        }
    }

    func deleteAll(entityName: String) {
        let context = backgroundContext
        context.performAndWait {
            let fetchRequest: NSFetchRequest<NSFetchRequestResult> = NSFetchRequest(entityName: entityName)
            let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
            deleteRequest.resultType = .resultTypeObjectIDs
            if let result = try? context.execute(deleteRequest) as? NSBatchDeleteResult,
               let objectIDs = result.result as? [NSManagedObjectID] {
                NSManagedObjectContext.mergeChanges(
                    fromRemoteContextSave: [NSDeletedObjectsKey: objectIDs],
                    into: [persistentContainer.viewContext]
                )
            }
        }
    }

    func entityCount(entityName: String) -> Int {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSNumber>(entityName: entityName)
        fetchRequest.resultType = .countResultType
        return (try? context.fetch(fetchRequest).first?.intValue) ?? 0
    }
}
