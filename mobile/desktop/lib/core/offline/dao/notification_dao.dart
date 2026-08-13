import 'package:drift/drift.dart';

import '../database.dart';

class NotificationDao {
  final AppDatabase _db;
  NotificationDao(this._db);

  Future<List<Notification>> getAll({
    bool? unreadOnly,
    String? type,
    int? limit,
    int? offset,
  }) async {
    final query = _db.select(_db.notifications);
    if (unreadOnly == true) {
      query.where((n) => n.isRead.equals(0));
    }
    if (type != null && type.isNotEmpty) {
      query.where((n) => n.type.equals(type));
    }
    if (limit != null) query.limit(limit, offset: offset);
    query.orderBy([(n) => OrderingTerm.desc(n.createdAt)]);
    return await query.get();
  }

  Future<Notification?> getById(String id) async {
    final query = _db.select(_db.notifications)..where((n) => n.id.equals(id));
    return await query.getSingleOrNull();
  }

  Future<void> upsert(NotificationsCompanion notification) async {
    await _db.into(_db.notifications).insertOnConflictUpdate(notification);
  }

  Future<void> upsertAll(List<NotificationsCompanion> notifications) async {
    await _db.batch((batch) {
      for (final n in notifications) {
        batch.insert(_db.notifications, n, mode: InsertMode.insertOrReplace);
      }
    });
  }

  Future<int> markAsRead(String id) async {
    return await (_db.update(_db.notifications)
      ..where((n) => n.id.equals(id))
    ).write(const NotificationsCompanion(isRead: Value(1)));
  }

  Future<int> markAllAsRead() async {
    return await (_db.update(_db.notifications)
      ..where((n) => n.isRead.equals(0))
    ).write(const NotificationsCompanion(isRead: Value(1)));
  }

  Future<int> delete(String id) async {
    return await (_db.delete(_db.notifications)..where((n) => n.id.equals(id))).go();
  }

  Future<int> deleteAll() async {
    return await _db.delete(_db.notifications).go();
  }

  Future<int> getUnreadCount() async {
    final countExpression = _db.notifications.id.count();
    final query = _db.selectOnly(_db.notifications)
      ..addColumns([countExpression])
      ..where(_db.notifications.isRead.equals(0));
    return (await query.getSingle()).read(countExpression) ?? 0;
  }

  Future<int> count() async {
    final countExpression = _db.notifications.id.count();
    final query = _db.selectOnly(_db.notifications)..addColumns([countExpression]);
    return (await query.getSingle()).read(countExpression) ?? 0;
  }

  Future<List<Notification>> getPendingSync() async {
    return await (_db.select(_db.notifications)
      ..where((n) => n.syncStatus.equals('pending'))
    ).get();
  }

  Future<void> markSynced(String id) async {
    await (_db.update(_db.notifications)
      ..where((n) => n.id.equals(id))
    ).write(const NotificationsCompanion(syncStatus: Value('synced')));
  }
}
