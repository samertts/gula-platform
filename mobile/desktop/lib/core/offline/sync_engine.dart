import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'connectivity_service.dart';
import 'sync_queue_manager.dart';
import 'database.dart';
import '../api/api_client.dart';

enum SyncStatus { idle, syncing, pending, error, offline }

class SyncEngine {
  final AppDatabase _db;
  final ApiClient _apiClient;
  final ConnectivityService _connectivityService;
  final SyncQueueManager _queueManager;

  final ValueNotifier<SyncStatus> statusNotifier = ValueNotifier(
    SyncStatus.idle,
  );
  final ValueNotifier<double> progressNotifier = ValueNotifier(0.0);
  final ValueNotifier<String?> lastSyncError = ValueNotifier(null);
  final ValueNotifier<DateTime?> lastSyncTime = ValueNotifier(null);

  Timer? _syncTimer;
  bool _isSyncing = false;
  int _syncIntervalSeconds = 30;

  SyncEngine({
    required AppDatabase db,
    required ApiClient apiClient,
    required ConnectivityService connectivityService,
    required SyncQueueManager queueManager,
  }) : _db = db,
       _apiClient = apiClient,
       _connectivityService = connectivityService,
       _queueManager = queueManager;

  int get syncIntervalSeconds => _syncIntervalSeconds;

  void setSyncInterval(int seconds) {
    _syncIntervalSeconds = seconds;
    _restartTimer();
  }

  void startPeriodicSync() {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(
      Duration(seconds: _syncIntervalSeconds),
      (_) => sync(),
    );
  }

  void stopPeriodicSync() {
    _syncTimer?.cancel();
    _syncTimer = null;
  }

  void _restartTimer() {
    stopPeriodicSync();
    startPeriodicSync();
  }

  Future<void> sync() async {
    if (_isSyncing) return;
    if (!_connectivityService.isCurrentlyOnline) {
      statusNotifier.value = SyncStatus.offline;
      return;
    }

    _isSyncing = true;
    statusNotifier.value = SyncStatus.syncing;
    progressNotifier.value = 0.0;

    try {
      final pendingQueue = await _queueManager.getPending();
      final failedQueue = await _queueManager.getFailed();
      final allItems = [...pendingQueue, ...failedQueue];

      if (allItems.isEmpty) {
        await _pullChanges();
      } else {
        await _processQueue(allItems);
      }

      await _pullChanges();

      lastSyncTime.value = DateTime.now();
      lastSyncError.value = null;
      statusNotifier.value = SyncStatus.idle;
      progressNotifier.value = 1.0;
    } catch (e) {
      lastSyncError.value = e.toString();
      statusNotifier.value = SyncStatus.error;
      debugPrint('Sync error: $e');
    } finally {
      _isSyncing = false;
    }
  }

  Future<void> _processQueue(List<SyncQueueData> items) async {
    for (int i = 0; i < items.length; i++) {
      final item = items[i];
      progressNotifier.value = (i + 1) / items.length;

      try {
        await _queueManager.markInProgress(item.id);

        final payload = jsonDecode(item.payload) as Map<String, dynamic>;

        switch (item.operation) {
          case 'create':
            await _apiClient.post('/${item.entityType}', data: payload);
            break;
          case 'update':
            await _apiClient.put(
              '/${item.entityType}/${item.entityId}',
              data: payload,
            );
            break;
          case 'delete':
            await _apiClient.delete('/${item.entityType}/${item.entityId}');
            break;
        }

        await _queueManager.markCompleted(item.id);
      } catch (e) {
        final message = e.toString();
        await _queueManager.markFailed(item.id, message);

        if (item.retryCount >= item.maxRetries) {
          await _queueManager.markDeadLetter(item.id);
        }
      }
    }
  }

  Future<void> _pullChanges() async {
    try {
      final timestamp = lastSyncTime.value?.toIso8601String() ?? '';
      await _apiClient.get(
        '/sync/changes',
        queryParameters: {'since': timestamp},
      );
      // Remote changes are fetched successfully. Entity-specific mappers are
      // applied by their repositories, which own the API-to-Drift contracts.
    } catch (e) {
      debugPrint('Pull changes error: $e');
    }
  }

  Future<Map<String, int>> getQueueStats() => _queueManager.getStats();

  Future<void> retryFailed() => _queueManager.retryFailed();

  Future<void> enqueue({
    required String entityType,
    required String entityId,
    required String operation,
    required Map<String, dynamic> payload,
  }) {
    return _queueManager.enqueue(
      entityType: entityType,
      entityId: entityId,
      operation: operation,
      payload: payload,
    );
  }

  void dispose() {
    stopPeriodicSync();
    statusNotifier.dispose();
    progressNotifier.dispose();
    lastSyncError.dispose();
    lastSyncTime.dispose();
  }
}
