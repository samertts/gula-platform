import 'package:drift/drift.dart';

import '../database.dart';

class OrderDao {
  final AppDatabase _db;
  OrderDao(this._db);

  Future<List<Order>> getAll({String? status, String? search, int? limit, int? offset}) async {
    final query = _db.select(_db.orders);
    if (status != null && status.isNotEmpty) {
      query.where((o) => o.status.equals(status));
    }
    if (search != null && search.isNotEmpty) {
      final pattern = '%$search%';
      query.where((o) =>
          o.orderNumber.like(pattern) |
          o.patientName.like(pattern) |
          o.id.like(pattern));
    }
    if (limit != null) query.limit(limit, offset: offset);
    query.orderBy([(o) => OrderingTerm.desc(o.createdAt)]);
    return await query.get();
  }

  Future<Order?> getById(String id) async {
    final query = _db.select(_db.orders)..where((o) => o.id.equals(id));
    return await query.getSingleOrNull();
  }

  Future<List<Order>> getByPatientId(String patientId) async {
    final query = _db.select(_db.orders)
      ..where((o) => o.patientId.equals(patientId))
      ..orderBy([(o) => OrderingTerm.desc(o.createdAt)]);
    return await query.get();
  }

  Future<void> upsert(OrderCompanion order) async {
    await _db.into(_db.orders).insertOnConflictUpdate(order);
  }

  Future<void> upsertAll(List<OrderCompanion> orders) async {
    await _db.batch((batch) {
      for (final o in orders) {
        batch.insert(_db.orders, o, mode: InsertMode.insertOrReplace);
      }
    });
  }

  Future<int> delete(String id) async {
    return await (_db.delete(_db.orders)..where((o) => o.id.equals(id))).go();
  }

  Future<int> count({String? status}) async {
    final query = _db.select(_db.orders);
    if (status != null) query.where((o) => o.status.equals(status));
    return await query.count();
  }

  Future<List<Order>> getPendingSync() async {
    return await (_db.select(_db.orders)
      ..where((o) => o.syncStatus.equals('pending'))
    ).get();
  }

  Future<void> markSynced(String id) async {
    await (_db.update(_db.orders)
      ..where((o) => o.id.equals(id))
    ).write(const OrderCompanion(syncStatus: Value('synced')));
  }
}
