import 'package:drift/drift.dart';

import '../database.dart';

class ResultDao {
  final AppDatabase _db;
  ResultDao(this._db);

  Future<List<Result>> getAll({
    String? status,
    String? orderId,
    String? patientId,
    bool? isCritical,
    int? limit,
    int? offset,
  }) async {
    final query = _db.select(_db.results);
    if (status != null) query.where((r) => r.status.equals(status));
    if (orderId != null) query.where((r) => r.orderId.equals(orderId));
    if (patientId != null) query.where((r) => r.patientId.equals(patientId));
    if (isCritical != null) {
      if (isCritical) {
        query.where((r) => r.isCritical.equals(1));
      }
    }
    if (limit != null) query.limit(limit, offset: offset);
    query.orderBy([(r) => OrderingTerm.desc(r.createdAt)]);
    return await query.get();
  }

  Future<Result?> getById(String id) async {
    final query = _db.select(_db.results)..where((r) => r.id.equals(id));
    return await query.getSingleOrNull();
  }

  Future<List<Result>> getByOrderId(String orderId) async {
    return await (_db.select(
      _db.results,
    )..where((r) => r.orderId.equals(orderId))).get();
  }

  Future<List<Result>> getCritical({String? labId}) async {
    final query = _db.select(_db.results)..where((r) => r.isCritical.equals(1));
    if (labId != null) query.where((r) => r.labId.equals(labId));
    query.orderBy([(r) => OrderingTerm.desc(r.createdAt)]);
    return await query.get();
  }

  Future<void> upsert(ResultsCompanion result) async {
    await _db.into(_db.results).insertOnConflictUpdate(result);
  }

  Future<void> upsertAll(List<ResultsCompanion> results) async {
    await _db.batch((batch) {
      for (final r in results) {
        batch.insert(_db.results, r, mode: InsertMode.insertOrReplace);
      }
    });
  }

  Future<int> delete(String id) async {
    return await (_db.delete(_db.results)..where((r) => r.id.equals(id))).go();
  }

  Future<int> count({String? status, bool? isCritical}) async {
    final countExpression = _db.results.id.count();
    final query = _db.selectOnly(_db.results)..addColumns([countExpression]);
    if (status != null) {
      query.where(_db.results.status.equals(status));
    }
    if (isCritical != null) {
      query.where(_db.results.isCritical.equals(isCritical ? 1 : 0));
    }
    return (await query.getSingle()).read(countExpression) ?? 0;
  }

  Future<List<Result>> getPendingSync() async {
    return await (_db.select(
      _db.results,
    )..where((r) => r.syncStatus.equals('pending'))).get();
  }

  Future<void> markSynced(String id) async {
    await (_db.update(_db.results)..where((r) => r.id.equals(id))).write(
      const ResultsCompanion(syncStatus: Value('synced')),
    );
  }
}
