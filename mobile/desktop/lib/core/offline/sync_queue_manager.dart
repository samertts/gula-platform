import 'dart:convert';

import 'package:drift/drift.dart';

import 'database.dart';

class SyncQueueManager {
  final AppDatabase _db;

  SyncQueueManager(this._db);

  Future<void> enqueue({
    required String entityType,
    required String entityId,
    required String operation,
    required Map<String, dynamic> payload,
    int maxRetries = 5,
  }) async {
    await _db.into(_db.syncQueue).insert(
      SyncQueueCompanion(
        entityType: Value(entityType),
        entityId: Value(entityId),
        operation: Value(operation),
        payload: Value(jsonEncode(payload)),
        status: const Value('pending'),
        retryCount: const Value(0),
        maxRetries: Value(maxRetries),
        createdAt: Value(DateTime.now().toIso8601String()),
        updatedAt: Value(DateTime.now().toIso8601String()),
      ),
    );
  }

  Future<List<SyncQueue>> getPending({int limit = 50}) async {
    final query = _db.select(_db.syncQueue)
      ..where((q) => q.status.equals('pending'))
      ..orderBy([(q) => OrderingTerm.asc(q.createdAt)])
      ..limit(limit);
    return await query.get();
  }

  Future<List<SyncQueue>> getFailed({int limit = 50}) async {
    final query = _db.select(_db.syncQueue)
      ..where((q) => q.status.equals('failed'))
      ..where((q) => q.retryCount < q.maxRetries)
      ..orderBy([(q) => OrderingTerm.asc(q.createdAt)])
      ..limit(limit);
    return await query.get();
  }

  Future<void> markInProgress(int id) async {
    await (_db.update(_db.syncQueue)
      ..where((q) => q.id.equals(id))
    ).write(const SyncQueueCompanion(
      status: Value('in_progress'),
      updatedAt: Value(''),
    ));
  }

  Future<void> markCompleted(int id) async {
    await (_db.delete(_db.syncQueue)..where((q) => q.id.equals(id))).go();
  }

  Future<void> markFailed(int id, String error) async {
    await (_db.update(_db.syncQueue)
      ..where((q) => q.id.equals(id))
    ).write(SyncQueueCompanion(
      status: const Value('failed'),
      retryCount: Value(_db.syncQueue.retryCount + 1),
      lastError: Value(error),
      updatedAt: Value(DateTime.now().toIso8601String()),
    ));
  }

  Future<void> markDeadLetter(int id) async {
    await (_db.update(_db.syncQueue)
      ..where((q) => q.id.equals(id))
    ).write(const SyncQueueCompanion(
      status: Value('dead_letter'),
      updatedAt: Value(''),
    ));
  }

  Future<int> getPendingCount() async {
    final query = _db.select(_db.syncQueue)
      ..where((q) => q.status.equals('pending'));
    return await query.count();
  }

  Future<int> getFailedCount() async {
    final query = _db.select(_db.syncQueue)
      ..where((q) => q.status.equals('failed'));
    return await query.count();
  }

  Future<void> clearDeadLetters() async {
    await (_db.delete(_db.syncQueue)
      ..where((q) => q.status.equals('dead_letter'))
    ).go();
  }

  Future<void> clearAll() async {
    await _db.delete(_db.syncQueue).go();
  }

  Future<Map<String, int>> getStats() async {
    final all = await _db.select(_db.syncQueue).get();
    final stats = <String, int>{
      'pending': 0,
      'in_progress': 0,
      'failed': 0,
      'dead_letter': 0,
    };
    for (final item in all) {
      stats[item.status] = (stats[item.status] ?? 0) + 1;
    }
    return stats;
  }

  Future<void> retryFailed() async {
    final failed = await getFailed();
    for (final item in failed) {
      await (_db.update(_db.syncQueue)
        ..where((q) => q.id.equals(item.id))
      ).write(const SyncQueueCompanion(status: Value('pending')));
    }
  }
}
