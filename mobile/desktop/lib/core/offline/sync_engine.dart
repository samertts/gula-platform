import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'connectivity_service.dart';
import 'sync_queue_manager.dart';
import 'conflict_resolver.dart';
import 'database.dart';
import '../api/api_client.dart';

enum SyncStatus { idle, syncing, pending, error, offline }

class SyncEngine {
  final AppDatabase _db;
  final ApiClient _apiClient;
  final ConnectivityService _connectivityService;
  final SyncQueueManager _queueManager;

  final ValueNotifier<SyncStatus> statusNotifier = ValueNotifier(SyncStatus.idle);
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
  })  : _db = db,
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

  Future<void> _processQueue(List<SyncQueue> items) async {
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
            await _apiClient.put('/${item.entityType}/${item.entityId}', data: payload);
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
      final response = await _apiClient.get(
        '/sync/changes',
        queryParameters: {'since': timestamp},
      );

      final data = response.data as Map<String, dynamic>?;
      if (data == null) return;

      await _db.transaction(() async {
        if (data['patients'] is List) {
          for (final p in data['patients'] as List) {
            if (p is Map<String, dynamic>) {
              await _db.into(_db.patients).insertOnConflictUpdate(
                PatientsCompanion.fromJson(p),
              );
            }
          }
        }
        if (data['orders'] is List) {
          for (final o in data['orders'] as List) {
            if (o is Map<String, dynamic>) {
              await _db.into(_db.orders).insertOnConflictUpdate(
                OrdersCompanion.fromJson(o),
              );
            }
          }
        }
        if (data['samples'] is List) {
          for (final s in data['samples'] as List) {
            if (s is Map<String, dynamic>) {
              await _db.into(_db.samples).insertOnConflictUpdate(
                SamplesCompanion.fromJson(s),
              );
            }
          }
        }
        if (data['results'] is List) {
          for (final r in data['results'] as List) {
            if (r is Map<String, dynamic>) {
              await _db.into(_db.results).insertOnConflictUpdate(
                ResultsCompanion.fromJson(r),
              );
            }
          }
        }
        if (data['notifications'] is List) {
          for (final n in data['notifications'] as List) {
            if (n is Map<String, dynamic>) {
              await _db.into(_db.notifications).insertOnConflictUpdate(
                NotificationsCompanion.fromJson(n),
              );
            }
          }
        }
      });
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
