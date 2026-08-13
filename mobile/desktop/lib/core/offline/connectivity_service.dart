import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

class ConnectivityService {
  final Connectivity _connectivity = Connectivity();
  final ValueNotifier<bool> isOnline = ValueNotifier(true);
  final ValueNotifier<ConnectivityResult> connectionType = ValueNotifier(
    ConnectivityResult.wifi,
  );

  StreamSubscription<List<ConnectivityResult>>? _subscription;
  bool _initialized = false;

  bool get isCurrentlyOnline => isOnline.value;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    try {
      final result = await _connectivity.checkConnectivity();
      _updateStatus(result);
    } catch (_) {
      isOnline.value = true;
    }

    _subscription = _connectivity.onConnectivityChanged.listen(_updateStatus);
  }

  void _updateStatus(List<ConnectivityResult> results) {
    final hasConnection = results.any(
      (r) =>
          r == ConnectivityResult.mobile ||
          r == ConnectivityResult.wifi ||
          r == ConnectivityResult.ethernet,
    );

    isOnline.value = hasConnection;

    if (results.isNotEmpty) {
      if (results.contains(ConnectivityResult.wifi)) {
        connectionType.value = ConnectivityResult.wifi;
      } else if (results.contains(ConnectivityResult.mobile)) {
        connectionType.value = ConnectivityResult.mobile;
      } else if (results.contains(ConnectivityResult.ethernet)) {
        connectionType.value = ConnectivityResult.ethernet;
      }
    }
  }

  Future<bool> checkConnectivity() async {
    try {
      final result = await _connectivity.checkConnectivity();
      _updateStatus(result);
      return isOnline.value;
    } catch (_) {
      return isOnline.value;
    }
  }

  void dispose() {
    _subscription?.cancel();
    isOnline.dispose();
    connectionType.dispose();
  }
}
