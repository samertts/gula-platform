import Foundation

enum ConflictResolutionStrategy: String, Codable, CaseIterable {
    case remoteWins = "remote-wins"
    case localWins = "local-wins"
    case lastWriteWins = "last-write-wins"
    case manualMerge = "manual-merge"
}

enum ConflictType {
    case versionConflict(entityId: String, localVersion: Int, remoteVersion: Int)
    case dataMismatch(entityId: String, field: String, localValue: AnyHashable, remoteValue: AnyHashable)
    case deletionConflict(entityId: String)
    case createConflict(entityId: String)

    var localizedDescription: String {
        switch self {
        case .versionConflict(let id, let local, let remote):
            return String(format: "conflict_version".localized, id, local, remote)
        case .dataMismatch(let id, let field, _, _):
            return String(format: "conflict_data".localized, id, field)
        case .deletionConflict(let id):
            return String(format: "conflict_deletion".localized, id)
        case .createConflict(let id):
            return String(format: "conflict_create".localized, id)
        }
    }
}

struct ConflictResolution {
    let conflict: ConflictType
    let strategy: ConflictResolutionStrategy
    let resolvedValue: Any?
    let timestamp: Date
}

actor ConflictResolver {
    static let shared = ConflictResolver()

    private var defaultStrategy: ConflictResolutionStrategy = .remoteWins
    private var strategyOverrides: [String: ConflictResolutionStrategy] = [:]

    func setDefaultStrategy(_ strategy: ConflictResolutionStrategy) {
        defaultStrategy = strategy
    }

    func setStrategy(for entityType: String, strategy: ConflictResolutionStrategy) {
        strategyOverrides[entityType] = strategy
    }

    func resolve(conflict: ConflictType, localData: Data?, remoteData: Data?) async -> ConflictResolution {
        let strategy = resolveStrategy(for: conflict)

        switch strategy {
        case .remoteWins:
            return ConflictResolution(
                conflict: conflict,
                strategy: .remoteWins,
                resolvedValue: remoteData,
                timestamp: Date()
            )

        case .localWins:
            return ConflictResolution(
                conflict: conflict,
                strategy: .localWins,
                resolvedValue: localData,
                timestamp: Date()
            )

        case .lastWriteWins:
            let resolved = resolveByTimestamp(localData: localData, remoteData: remoteData)
            return ConflictResolution(
                conflict: conflict,
                strategy: .lastWriteWins,
                resolvedValue: resolved,
                timestamp: Date()
            )

        case .manualMerge:
            return ConflictResolution(
                conflict: conflict,
                strategy: .manualMerge,
                resolvedValue: nil,
                timestamp: Date()
            )
        }
    }

    func detectConflict(localEntity: NSManagedObject, remoteJSON: [String: Any]) -> ConflictType? {
        guard let entityId = localEntity.value(forKey: "id") as? Int else { return nil }
        let localVersion = localEntity.value(forKey: "version") as? Int ?? 0
        let remoteVersion = remoteJSON["version"] as? Int ?? 0

        if remoteVersion > localVersion + 1 {
            return .versionConflict(
                entityId: String(entityId),
                localVersion: localVersion,
                remoteVersion: remoteVersion
            )
        }

        return nil
    }

    private func resolveStrategy(for conflict: ConflictType) -> ConflictResolutionStrategy {
        let entityType: String
        switch conflict {
        case .versionConflict(let id, _, _):
            entityType = extractEntityType(from: id)
        case .dataMismatch(let id, _, _, _):
            entityType = extractEntityType(from: id)
        case .deletionConflict(let id):
            entityType = extractEntityType(from: id)
        case .createConflict(let id):
            entityType = extractEntityType(from: id)
        }

        return strategyOverrides[entityType] ?? defaultStrategy
    }

    private func resolveByTimestamp(localData: Data?, remoteData: Data?) -> Data? {
        guard let local = localData, let remote = remoteData else {
            return localData ?? remoteData
        }

        let localTimestamp = extractTimestamp(from: local)
        let remoteTimestamp = extractTimestamp(from: remote)

        return localTimestamp >= remoteTimestamp ? local : remote
    }

    private func extractTimestamp(from data: Data) -> Date {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let timestampString = json["updatedAt"] as? String ?? json["updated_at"] as? String else {
            return .distantPast
        }
        return ISO8601DateFormatter().date(from: timestampString) ?? .distantPast
    }

    private func extractEntityType(from id: String) -> String {
        if id.contains("patient") { return "patient" }
        if id.contains("order") { return "order" }
        if id.contains("sample") { return "sample" }
        if id.contains("result") { return "result" }
        return "unknown"
    }
}
