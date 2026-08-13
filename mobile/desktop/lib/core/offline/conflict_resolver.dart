enum ConflictStrategy { localWins, remoteWins, lastWriterWins, manual, merge }

class ConflictRecord {
  final String entityType;
  final String entityId;
  final Map<String, dynamic> localData;
  final Map<String, dynamic> remoteData;
  final DateTime localUpdatedAt;
  final DateTime remoteUpdatedAt;

  const ConflictRecord({
    required this.entityType,
    required this.entityId,
    required this.localData,
    required this.remoteData,
    required this.localUpdatedAt,
    required this.remoteUpdatedAt,
  });
}

class ConflictResolution {
  final bool resolved;
  final Map<String, dynamic>? resolvedData;
  final ConflictStrategy? strategy;
  final String? detail;

  const ConflictResolution({
    this.resolved = false,
    this.resolvedData,
    this.strategy,
    this.detail,
  });

  factory ConflictResolution.automatic(
    Map<String, dynamic> data,
    ConflictStrategy strategy,
  ) {
    return ConflictResolution(
      resolved: true,
      resolvedData: data,
      strategy: strategy,
    );
  }

  factory ConflictResolution.pending(String detail) {
    return ConflictResolution(resolved: false, detail: detail);
  }
}

class ConflictResolver {
  final ConflictStrategy defaultStrategy;

  ConflictResolver({this.defaultStrategy = ConflictStrategy.lastWriterWins});

  ConflictResolution resolve(
    ConflictRecord record, {
    ConflictStrategy? strategy,
  }) {
    final s = strategy ?? defaultStrategy;
    switch (s) {
      case ConflictStrategy.localWins:
        return ConflictResolution.automatic(
          Map<String, dynamic>.from(record.localData),
          ConflictStrategy.localWins,
        );
      case ConflictStrategy.remoteWins:
        return ConflictResolution.automatic(
          Map<String, dynamic>.from(record.remoteData),
          ConflictStrategy.remoteWins,
        );
      case ConflictStrategy.lastWriterWins:
        return _resolveLww(record);
      case ConflictStrategy.manual:
        return ConflictResolution.pending(
          'Manual resolution required for ${record.entityType}:${record.entityId}',
        );
      case ConflictStrategy.merge:
        return _resolveMerge(record);
    }
  }

  ConflictResolution _resolveLww(ConflictRecord record) {
    if (record.localUpdatedAt.isAfter(record.remoteUpdatedAt)) {
      return ConflictResolution.automatic(
        Map<String, dynamic>.from(record.localData),
        ConflictStrategy.lastWriterWins,
      );
    }
    return ConflictResolution.automatic(
      Map<String, dynamic>.from(record.remoteData),
      ConflictStrategy.lastWriterWins,
    );
  }

  ConflictResolution _resolveMerge(ConflictRecord record) {
    final merged = Map<String, dynamic>.from(record.remoteData);

    for (final key in record.localData.keys) {
      if (!merged.containsKey(key)) {
        merged[key] = record.localData[key];
        continue;
      }

      final localVal = record.localData[key];
      final remoteVal = record.remoteData[key];

      if (localVal == null && remoteVal == null) continue;
      if (localVal == null) continue;
      if (remoteVal == null) {
        merged[key] = localVal;
        continue;
      }

      if (key.endsWith('_at') || key == 'updatedAt' || key == 'createdAt') {
        merged[key] = record.localUpdatedAt.isAfter(record.remoteUpdatedAt)
            ? localVal
            : remoteVal;
        continue;
      }

      if (localVal is List && remoteVal is List) {
        final mergedList = [...remoteVal];
        for (final item in localVal) {
          if (!mergedList.contains(item)) {
            mergedList.add(item);
          }
        }
        merged[key] = mergedList;
      } else if (localVal is Map && remoteVal is Map) {
        merged[key] = {...remoteVal as Map, ...localVal as Map};
      }
    }

    return ConflictResolution.automatic(merged, ConflictStrategy.merge);
  }

  static bool hasConflict(
    Map<String, dynamic> local,
    Map<String, dynamic> remote,
  ) {
    if (local.isEmpty || remote.isEmpty) return false;

    final localUpdated =
        local['updated_at'] as String? ?? local['updatedAt'] as String?;
    final remoteUpdated =
        remote['updated_at'] as String? ?? remote['updatedAt'] as String?;

    if (localUpdated == null || remoteUpdated == null) return false;

    final localTime = DateTime.tryParse(localUpdated);
    final remoteTime = DateTime.tryParse(remoteUpdated);

    if (localTime == null || remoteTime == null) return false;

    return localTime != remoteTime;
  }
}
