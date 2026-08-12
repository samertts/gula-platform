import 'package:flutter/foundation.dart';

import 'sync_engine.dart';
import 'connectivity_service.dart';

class SyncProvider extends ChangeNotifier {
  final SyncEngine _syncEngine;
  final ConnectivityService _connectivityService;

  SyncProvider(this._syncEngine, this._connectivityService) {
    _syncEngine.statusNotifier.addListener(notifyListeners);
    _syncEngine.progressNotifier.addListener(notifyListeners);
    _syncEngine.lastSyncError.addListener(notifyListeners);
    _syncEngine.lastSyncTime.addListener(notifyListeners);
    _connectivityService.isOnline.addListener(notifyListeners);
  }

  SyncEngine get engine => _syncEngine;
  SyncStatus get status => _syncEngine.statusNotifier.value;
  double get progress => _syncEngine.progressNotifier.value;
  String? get lastError => _syncEngine.lastSyncError.value;
  DateTime? get lastSyncTime => _syncEngine.lastSyncTime.value;
  bool get isOnline => _connectivityService.isCurrentlyOnline;
  bool get isSyncing => status == SyncStatus.syncing;
  bool get hasError => status == SyncStatus.error;
  bool get isOffline => status == SyncStatus.offline;

  Future<void> sync() => _syncEngine.sync();
  Future<void> retryFailed() => _syncEngine.retryFailed();
  void startPeriodicSync() => _syncEngine.startPeriodicSync();
  void stopPeriodicSync() => _syncEngine.stopPeriodicSync();

  @override
  void dispose() {
    _syncEngine.statusNotifier.removeListener(notifyListeners);
    _syncEngine.progressNotifier.removeListener(notifyListeners);
    _syncEngine.lastSyncError.removeListener(notifyListeners);
    _syncEngine.lastSyncTime.removeListener(notifyListeners);
    _connectivityService.isOnline.removeListener(notifyListeners);
    super.dispose();
  }
}
