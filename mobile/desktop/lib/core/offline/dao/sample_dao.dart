import 'package:drift/drift.dart';

import '../database.dart';

class SampleDao {
  final AppDatabase _db;
  SampleDao(this._db);

  Future<List<Sample>> getAll({String? status, String? search, int? limit, int? offset}) async {
    final query = _db.select(_db.samples);
    if (status != null && status.isNotEmpty) {
      query.where((s) => s.status.equals(status));
    }
    if (search != null && search.isNotEmpty) {
      final pattern = '%$search%';
      query.where((s) =>
          s.barcode.like(pattern) |
          s.id.like(pattern));
    }
    if (limit != null) query.limit(limit, offset: offset);
    query.orderBy([(s) => OrderingTerm.desc(s.createdAt)]);
    return await query.get();
  }

  Future<Sample?> getById(String id) async {
    final query = _db.select(_db.samples)..where((s) => s.id.equals(id));
    return await query.getSingleOrNull();
  }

  Future<Sample?> getByBarcode(String barcode) async {
    final query = _db.select(_db.samples)..where((s) => s.barcode.equals(barcode));
    return await query.getSingleOrNull();
  }

  Future<List<Sample>> getByOrderId(String orderId) async {
    return await (_db.select(_db.samples)
      ..where((s) => s.orderId.equals(orderId))
    ).get();
  }

  Future<void> upsert(SampleCompanion sample) async {
    await _db.into(_db.samples).insertOnConflictUpdate(sample);
  }

  Future<void> upsertAll(List<SampleCompanion> samples) async {
    await _db.batch((batch) {
      for (final s in samples) {
        batch.insert(_db.samples, s, mode: InsertMode.insertOrReplace);
      }
    });
  }

  Future<int> delete(String id) async {
    return await (_db.delete(_db.samples)..where((s) => s.id.equals(id))).go();
  }

  Future<int> count({String? status}) async {
    final query = _db.select(_db.samples);
    if (status != null) query.where((s) => s.status.equals(status));
    return await query.count();
  }

  Future<List<Sample>> getPendingSync() async {
    return await (_db.select(_db.samples)
      ..where((s) => s.syncStatus.equals('pending'))
    ).get();
  }

  Future<void> markSynced(String id) async {
    await (_db.update(_db.samples)
      ..where((s) => s.id.equals(id))
    ).write(const SampleCompanion(syncStatus: Value('synced')));
  }
}
