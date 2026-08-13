import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_manager.dart';
import '../auth/auth_provider.dart';
import '../auth/secure_storage.dart';
import '../offline/database.dart';
import '../offline/dao/notification_dao.dart';
import '../offline/dao/order_dao.dart';
import '../offline/dao/patient_dao.dart';
import '../offline/dao/result_dao.dart';
import '../offline/dao/sample_dao.dart';
import '../offline/connectivity_service.dart';
import '../offline/sync_queue_manager.dart';
import '../offline/sync_engine.dart';
import '../offline/sync_provider.dart';
import '../theme/theme_provider.dart';

final themeProvider = ChangeNotifierProvider<ThemeProvider>((ref) {
  return ThemeProvider();
});

final secureStorageProvider = Provider<SecureStorage>((ref) {
  return SecureStorage();
});

final authManagerProvider = Provider<AuthManager>((ref) {
  return AuthManager();
});

final authProviderProvider = ChangeNotifierProvider<AuthProvider>((ref) {
  final manager = ref.watch(authManagerProvider);
  return AuthProvider(manager);
});

final databaseProvider = Provider<AppDatabase>((ref) {
  return AppDatabase();
});

final connectivityServiceProvider = Provider<ConnectivityService>((ref) {
  return ConnectivityService();
});

final syncQueueManagerProvider = Provider<SyncQueueManager>((ref) {
  final db = ref.watch(databaseProvider);
  return SyncQueueManager(db);
});

final syncEngineProvider = Provider<SyncEngine>((ref) {
  final db = ref.watch(databaseProvider);
  final authManager = ref.watch(authManagerProvider);
  final connectivity = ref.watch(connectivityServiceProvider);
  final queueManager = ref.watch(syncQueueManagerProvider);
  return SyncEngine(
    db: db,
    apiClient: authManager.apiClient,
    connectivityService: connectivity,
    queueManager: queueManager,
  );
});

final syncProviderProvider = ChangeNotifierProvider<SyncProvider>((ref) {
  final engine = ref.watch(syncEngineProvider);
  final connectivity = ref.watch(connectivityServiceProvider);
  return SyncProvider(engine, connectivity);
});

final patientDaoProvider = Provider<PatientDao>((ref) {
  final db = ref.watch(databaseProvider);
  return PatientDao(db);
});

final orderDaoProvider = Provider<OrderDao>((ref) {
  final db = ref.watch(databaseProvider);
  return OrderDao(db);
});

final sampleDaoProvider = Provider<SampleDao>((ref) {
  final db = ref.watch(databaseProvider);
  return SampleDao(db);
});

final resultDaoProvider = Provider<ResultDao>((ref) {
  final db = ref.watch(databaseProvider);
  return ResultDao(db);
});

final notificationDaoProvider = Provider<NotificationDao>((ref) {
  final db = ref.watch(databaseProvider);
  return NotificationDao(db);
});
