import 'package:drift/drift.dart';

import '../database.dart';

class PatientDao {
  final AppDatabase _db;
  PatientDao(this._db);

  Future<List<Patient>> getAll({String? search, int? limit, int? offset}) async {
    final query = _db.select(_db.patients)
      ..where((p) => p.deletedAt.isNull());
    if (search != null && search.isNotEmpty) {
      final pattern = '%$search%';
      query.where((p) =>
          p.fullName.like(pattern) |
          p.nationalId.like(pattern) |
          p.phone.like(pattern) |
          p.id.like(pattern));
    }
    if (limit != null) query.limit(limit, offset: offset);
    query.orderBy([(p) => OrderingTerm.desc(p.updatedAt)]);
    return await query.get();
  }

  Future<Patient?> getById(String id) async {
    final query = _db.select(_db.patients)..where((p) => p.id.equals(id));
    return await query.getSingleOrNull();
  }

  Future<Patient?> getByNationalId(String nationalId) async {
    final query = _db.select(_db.patients)..where((p) => p.nationalId.equals(nationalId));
    return await query.getSingleOrNull();
  }

  Future<List<Patient>> search(String query) async {
    final pattern = '%$query%';
    final stmt = _db.select(_db.patients)
      ..where((p) =>
          p.fullName.like(pattern) |
          p.nationalId.like(pattern) |
          p.phone.like(pattern));
    stmt.limit(50);
    return await stmt.get();
  }

  Future<void> upsert(PatientsCompanion patient) async {
    await _db.into(_db.patients).insertOnConflictUpdate(patient);
  }

  Future<void> upsertAll(List<PatientsCompanion> patients) async {
    await _db.batch((batch) {
      for (final p in patients) {
        batch.insert(_db.patients, p, mode: InsertMode.insertOrReplace);
      }
    });
  }

  Future<int> delete(String id) async {
    return await (_db.delete(_db.patients)..where((p) => p.id.equals(id))).go();
  }

  Future<int> softDelete(String id) async {
    return await (_db.update(_db.patients)
      ..where((p) => p.id.equals(id))
    ).write(const PatientsCompanion(deletedAt: Value(null)));
  }

  Future<int> count({String? search}) async {
    final countExpression = _db.patients.id.count();
    final query = _db.selectOnly(_db.patients)..addColumns([countExpression]);
    if (search != null && search.isNotEmpty) {
      final pattern = '%$search%';
      query.where(
        _db.patients.fullName.like(pattern) |
            _db.patients.nationalId.like(pattern),
      );
    }
    return (await query.getSingle()).read(countExpression) ?? 0;
  }

  Future<List<Patient>> getPendingSync() async {
    final query = _db.select(_db.patients)
      ..where((p) => p.syncStatus.equals('pending'));
    return await query.get();
  }

  Future<void> markSynced(String id) async {
    await (_db.update(_db.patients)
      ..where((p) => p.id.equals(id))
    ).write(const PatientsCompanion(syncStatus: Value('synced')));
  }
}
