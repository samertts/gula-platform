import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

const _kQueueKey = 'gula_offline_queue';
const _kQueueMetaKey = 'gula_offline_queue_meta';
const _kMaxQueueSize = 1000;

enum QueueEntryStatus { pending, processing, failed, completed }

class OfflineQueueEntry {
  final String id;
  final String method;
  final String path;
  final Map<String, dynamic>? data;
  final Map<String, String>? headers;
  final DateTime createdAt;
  final int retryCount;
  final QueueEntryStatus status;
  final String? lastError;

  const OfflineQueueEntry({
    required this.id,
    required this.method,
    required this.path,
    this.data,
    this.headers,
    required this.createdAt,
    this.retryCount = 0,
    this.status = QueueEntryStatus.pending,
    this.lastError,
  });

  OfflineQueueEntry copyWith({
    int? retryCount,
    QueueEntryStatus? status,
    String? lastError,
  }) {
    return OfflineQueueEntry(
      id: id,
      method: method,
      path: path,
      data: data,
      headers: headers,
      createdAt: createdAt,
      retryCount: retryCount ?? this.retryCount,
      status: status ?? this.status,
      lastError: lastError ?? this.lastError,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'method': method,
    'path': path,
    'data': data,
    'headers': headers,
    'createdAt': createdAt.toIso8601String(),
    'retryCount': retryCount,
    'status': status.index,
    'lastError': lastError,
  };

  factory OfflineQueueEntry.fromJson(Map<String, dynamic> json) => OfflineQueueEntry(
    id: json['id'] as String,
    method: json['method'] as String,
    path: json['path'] as String,
    data: json['data'] as Map<String, dynamic>?,
    headers: (json['headers'] as Map<String, dynamic>?)
        ?.map((k, v) => MapEntry(k, v as String)),
    createdAt: DateTime.parse(json['createdAt'] as String),
    retryCount: json['retryCount'] as int? ?? 0,
    status: QueueEntryStatus.values[json['status'] as int? ?? 0],
    lastError: json['lastError'] as String?,
  );
}

class OfflineSyncManager {
  final Connectivity _connectivity = Connectivity();
  final Dio _dio;
  final Uuid _uuid = const Uuid();
  final ValueNotifier<bool> isOnline = ValueNotifier(true);
  final ValueNotifier<int> pendingCount = ValueNotifier(0);
  final ValueNotifier<SyncStatus> syncStatus = ValueNotifier(SyncStatus.idle);

  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;
  List<OfflineQueueEntry> _queue = [];
  bool _processing = false;
  int _maxRetries = 5;

  OfflineSyncManager({required Dio dio, this._maxRetries = 5}) : _dio = dio;

  Future<void> init() async {
    await _loadQueue();
    _connectivitySub = _connectivity.onConnectivityChanged.listen(_onConnectivityChange);
    final results = await _connectivity.checkConnectivity();
    _onConnectivityChange(results);
  }

  void _onConnectivityChange(List<ConnectivityResult> results) {
    final online = results.any((r) => r != ConnectivityResult.none);
    isOnline.value = online;
    if (online) {
      processQueue();
    }
  }

  Future<void> _loadQueue() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_kQueueKey);
      if (raw != null) {
        final list = jsonDecode(raw) as List;
        _queue = list.map((e) => OfflineQueueEntry.fromJson(e as Map<String, dynamic>)).toList();
        _queue.removeWhere((e) => e.status == QueueEntryStatus.completed);
      }
      pendingCount.value = _queue.where((e) => e.status == QueueEntryStatus.pending).length;
    } catch (_) {}
  }

  Future<void> _persistQueue() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final data = _queue.map((e) => e.toJson()).toList();
      await prefs.setString(_kQueueKey, jsonEncode(data));
      pendingCount.value = _queue.where((e) => e.status == QueueEntryStatus.pending).length;
    } catch (_) {}
  }

  Future<void> enqueue({
    required String method,
    required String path,
    Map<String, dynamic>? data,
    Map<String, String>? headers,
  }) async {
    if (_queue.length >= _kMaxQueueSize) {
      _queue.removeWhere((e) => e.status == QueueEntryStatus.completed);
      if (_queue.length >= _kMaxQueueSize) {
        _queue.removeAt(0);
      }
    }

    final entry = OfflineQueueEntry(
      id: _uuid.v4(),
      method: method.toUpperCase(),
      path: path,
      data: data,
      headers: headers,
      createdAt: DateTime.now(),
    );
    _queue.add(entry);
    await _persistQueue();
  }

  Future<void> processQueue() async {
    if (_processing || !isOnline.value) return;
    _processing = true;
    syncStatus.value = SyncStatus.syncing;

    try {
      final pending = List<OfflineQueueEntry>.from(
        _queue.where((e) => e.status == QueueEntryStatus.pending),
      );

      for (final entry in pending) {
        if (!isOnline.value) break;

        final index = _queue.indexOf(entry);
        if (index == -1) continue;

        _queue[index] = entry.copyWith(status: QueueEntryStatus.processing);
        await _persistQueue();

        try {
          await _executeEntry(entry);
          _queue[index] = entry.copyWith(status: QueueEntryStatus.completed);
          await _persistQueue();
        } catch (e) {
          final newRetries = entry.retryCount + 1;
          if (newRetries >= _maxRetries) {
            _queue[index] = entry.copyWith(
              status: QueueEntryStatus.failed,
              retryCount: newRetries,
              lastError: e.toString(),
            );
          } else {
            _queue[index] = entry.copyWith(
              status: QueueEntryStatus.pending,
              retryCount: newRetries,
              lastError: e.toString(),
            );
          }
          await _persistQueue();
        }
      }

      final failed = _queue.where((e) => e.status == QueueEntryStatus.failed).length;
      if (failed > 0) {
        syncStatus.value = SyncStatus.partial;
      } else {
        syncStatus.value = SyncStatus.completed;
      }
    } finally {
      _processing = false;
    }
  }

  Future<void> _executeEntry(OfflineQueueEntry entry) async {
    final options = Options(
      method: entry.method,
      headers: Map<String, dynamic>.from(entry.headers ?? {}),
    );

    switch (entry.method) {
      case 'GET':
        await _dio.get(entry.path, options: options);
      case 'POST':
        await _dio.post(entry.path, data: entry.data, options: options);
      case 'PUT':
        await _dio.put(entry.path, data: entry.data, options: options);
      case 'PATCH':
        await _dio.patch(entry.path, data: entry.data, options: options);
      case 'DELETE':
        await _dio.delete(entry.path, options: options);
    }
  }

  Future<List<OfflineQueueEntry>> getFailedEntries() async {
    return _queue.where((e) => e.status == QueueEntryStatus.failed).toList();
  }

  Future<void> clearFailedEntries() async {
    _queue.removeWhere((e) => e.status == QueueEntryStatus.failed);
    await _persistQueue();
  }

  Future<void> clearAll() async {
    _queue.clear();
    await _persistQueue();
  }

  Future<void> retryFailed() async {
    for (int i = 0; i < _queue.length; i++) {
      if (_queue[i].status == QueueEntryStatus.failed) {
        _queue[i] = _queue[i].copyWith(
          status: QueueEntryStatus.pending,
          retryCount: 0,
          lastError: null,
        );
      }
    }
    await _persistQueue();
    processQueue();
  }

  void dispose() {
    _connectivitySub?.cancel();
  }
}

enum SyncStatus { idle, syncing, completed, partial }
