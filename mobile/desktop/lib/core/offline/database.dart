import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

part 'database.g.dart';

class Patients extends Table {
  TextColumn get id => text()();
  TextColumn get labId => text().nullable()();
  TextColumn get nationalId => text().nullable()();
  TextColumn get sndhsHealthId => text().nullable()();
  TextColumn get firstName => text()();
  TextColumn get fatherName => text().nullable()();
  TextColumn get grandFatherName => text().nullable()();
  TextColumn get lastName => text().nullable()();
  TextColumn get fullName => text()();
  TextColumn get motherName => text().nullable()();
  TextColumn get gender => text()();
  TextColumn get dateOfBirth => text().nullable()();
  TextColumn get phone => text().nullable()();
  TextColumn get email => text().nullable()();
  TextColumn get address => text().nullable()();
  TextColumn get city => text().nullable()();
  TextColumn get bloodGroup => text().nullable()();
  TextColumn get maritalStatus => text().nullable()();
  TextColumn get occupation => text().nullable()();
  TextColumn get photoUrl => text().nullable()();
  TextColumn get insuranceProvider => text().nullable()();
  TextColumn get insuranceNumber => text().nullable()();
  TextColumn get notes => text().nullable()();
  TextColumn get tags => text().nullable()();
  TextColumn get qrToken => text().nullable()();
  TextColumn get createdAt => text()();
  TextColumn get updatedAt => text()();
  TextColumn get deletedAt => text().nullable()();
  TextColumn get syncStatus => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class Orders extends Table {
  TextColumn get id => text()();
  TextColumn get labId => text()();
  TextColumn get patientId => text()();
  TextColumn get patientName => text()();
  TextColumn get orderNumber => text()();
  TextColumn get status => text()();
  TextColumn get priority => text().nullable()();
  TextColumn get testTypes => text()();
  TextColumn get doctorName => text().nullable()();
  TextColumn get doctorId => text().nullable()();
  TextColumn get diagnosis => text().nullable()();
  TextColumn get notes => text().nullable()();
  TextColumn get requestedBy => text().nullable()();
  TextColumn get collectedBy => text().nullable()();
  TextColumn get collectionDate => text().nullable()();
  TextColumn get receivedDate => text().nullable()();
  TextColumn get completedDate => text().nullable()();
  TextColumn get createdAt => text()();
  TextColumn get updatedAt => text()();
  TextColumn get syncStatus => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class Samples extends Table {
  TextColumn get id => text()();
  TextColumn get labId => text()();
  TextColumn get orderId => text()();
  TextColumn get patientId => text()();
  TextColumn get sampleType => text()();
  TextColumn get barcode => text()();
  TextColumn get status => text()();
  TextColumn get containerType => text().nullable()();
  RealColumn get volume => real().nullable()();
  TextColumn get collectedAt => text().nullable()();
  TextColumn get collectedBy => text().nullable()();
  TextColumn get receivedAt => text().nullable()();
  TextColumn get receivedBy => text().nullable()();
  TextColumn get processedAt => text().nullable()();
  TextColumn get processedBy => text().nullable()();
  TextColumn get storageLocation => text().nullable()();
  TextColumn get rejectionReason => text().nullable()();
  TextColumn get notes => text().nullable()();
  TextColumn get createdAt => text()();
  TextColumn get updatedAt => text()();
  TextColumn get syncStatus => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class Results extends Table {
  TextColumn get id => text()();
  TextColumn get labId => text()();
  TextColumn get orderId => text()();
  TextColumn get sampleId => text().nullable()();
  TextColumn get patientId => text()();
  TextColumn get testCode => text()();
  TextColumn get testName => text()();
  TextColumn get result => text()();
  TextColumn get unit => text().nullable()();
  TextColumn get referenceRange => text().nullable()();
  TextColumn get flag => text().nullable()();
  IntColumn get isAbnormal => integer()();
  IntColumn get isCritical => integer()();
  TextColumn get validatedBy => text().nullable()();
  TextColumn get validatedAt => text().nullable()();
  TextColumn get performedBy => text().nullable()();
  TextColumn get instrumentId => text().nullable()();
  TextColumn get notes => text().nullable()();
  TextColumn get status => text()();
  TextColumn get createdAt => text()();
  TextColumn get updatedAt => text()();
  TextColumn get syncStatus => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class Notifications extends Table {
  TextColumn get id => text()();
  TextColumn get labId => text().nullable()();
  TextColumn get title => text()();
  TextColumn get body => text()();
  TextColumn get type => text()();
  TextColumn get severity => text()();
  TextColumn get entityType => text().nullable()();
  TextColumn get entityId => text().nullable()();
  IntColumn get isRead => integer()();
  IntColumn get isActioned => integer()();
  TextColumn get createdAt => text()();
  TextColumn get syncStatus => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class SyncQueue extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get entityType => text()();
  TextColumn get entityId => text()();
  TextColumn get operation => text()();
  TextColumn get payload => text()();
  TextColumn get status => text()();
  IntColumn get retryCount => integer()();
  IntColumn get maxRetries => integer()();
  TextColumn get createdAt => text()();
  TextColumn get updatedAt => text()();
  TextColumn get lastError => text().nullable()();
}

class CacheEntries extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();
  TextColumn get expiresAt => text()();
  TextColumn get createdAt => text()();

  @override
  Set<Column> get primaryKey => {key};
}

@DriftDatabase(tables: [
  Patients,
  Orders,
  Samples,
  Results,
  Notifications,
  SyncQueue,
  CacheEntries,
])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration {
    return MigrationStrategy(
      onCreate: (Migrator m) async {
        await m.createAll();
      },
      onUpgrade: (Migrator m, int from, int to) async {},
      beforeOpen: (details) async {
        if (details.wasCreated) {
          await _seedDefaultData();
        }
      },
    );
  }

  Future<void> _seedDefaultData() async {}

  Future<void> clearAll() async {
    await transaction(() async {
      for (final table in allTables) {
        await delete(table).go();
      }
    });
  }

  Future<Map<String, int>> getTableCounts() async {
    return {
      'patients': (await customSelect('SELECT COUNT(*) FROM patients').getSingle()).read<int>(0),
      'orders': (await customSelect('SELECT COUNT(*) FROM orders').getSingle()).read<int>(0),
      'samples': (await customSelect('SELECT COUNT(*) FROM samples').getSingle()).read<int>(0),
      'results': (await customSelect('SELECT COUNT(*) FROM results').getSingle()).read<int>(0),
      'notifications': (await customSelect('SELECT COUNT(*) FROM notifications').getSingle()).read<int>(0),
      'syncQueue': (await customSelect('SELECT COUNT(*) FROM sync_queue').getSingle()).read<int>(0),
    };
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'gula_desktop.db'));
    return NativeDatabase(file);
  });
}
