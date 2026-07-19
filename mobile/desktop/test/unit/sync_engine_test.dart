import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import '../../lib/core/offline/sync_engine.dart';
import '../../lib/core/offline/sync_queue_manager.dart';
import '../../lib/core/offline/connectivity_service.dart';
import '../../lib/core/offline/conflict_resolver.dart';
import '../../lib/core/offline/database.dart';

import 'sync_engine_test.mocks.dart';

@GenerateMocks([ConnectivityService, SyncQueueManager, ConflictResolver, AppDatabase, PatientDao, OrderDao, SampleDao, ResultDao, NotificationDao])
void main() {
  late MockConnectivityService mockConnectivity;
  late MockSyncQueueManager mockQueueManager;
  late MockConflictResolver mockResolver;
  late AppDatabase mockDb;
  late SyncEngine syncEngine;

  setUp(() {
    mockConnectivity = MockConnectivityService();
    mockQueueManager = MockSyncQueueManager();
    mockResolver = MockConflictResolver();
    mockDb = MockAppDatabase();
    syncEngine = SyncEngine(
      database: mockDb,
      connectivityService: mockConnectivity,
      queueManager: mockQueueManager,
      conflictResolver: mockResolver,
    );
  });

  group('SyncEngine', () {
    test('initial state is idle and not syncing', () {
      expect(syncEngine.syncState, SyncState.idle);
      expect(syncEngine.isSyncing, false);
    });

    test('sync is a no-op when offline', () async {
      when(mockConnectivity.isConnected).thenReturn(false);

      await syncEngine.sync();

      expect(syncEngine.syncState, SyncState.idle);
    });
  });
}
