import 'dart:async';

import 'package:flutter/foundation.dart';

enum UpdateStatus { idle, checking, available, downloading, readyToInstall, error, upToDate }

/// Update facade retained for the desktop UI while native update providers are
/// configured per release channel. It never downloads or installs software
/// without an explicitly integrated, platform-reviewed updater.
class AutoUpdater {
  final ValueNotifier<UpdateStatus> statusNotifier = ValueNotifier(UpdateStatus.idle);
  final ValueNotifier<double> downloadProgress = ValueNotifier(0.0);
  final ValueNotifier<String?> updateVersion = ValueNotifier(null);
  final ValueNotifier<String?> updateError = ValueNotifier(null);

  UpdateStatus _status = UpdateStatus.idle;
  bool _initialized = false;
  Timer? _checkTimer;
  String? _feedUrl;

  bool get isInitialized => _initialized;
  UpdateStatus get status => _status;

  Future<void> initialize({
    String? feedUrl,
    int checkIntervalHours = 6,
  }) async {
    if (_initialized) return;
    _initialized = true;
    _feedUrl = feedUrl;
    _checkTimer = Timer.periodic(
      Duration(hours: checkIntervalHours),
      (_) => checkForUpdates(),
    );
  }

  Future<bool> checkForUpdates() async {
    _setStatus(UpdateStatus.checking);
    // Native package APIs differ by platform and release channel. Until a
    // signed provider is configured, report a deterministic no-update state.
    _setStatus(UpdateStatus.upToDate);
    return false;
  }

  Future<void> downloadUpdate() async {
    updateError.value = 'Automatic downloads are not configured for this release channel.';
    _setStatus(UpdateStatus.error);
  }

  Future<void> installUpdate() async {
    updateError.value = 'Automatic installation is not configured for this release channel.';
    _setStatus(UpdateStatus.error);
  }

  Future<void> setFeedUrl(String url) async {
    _feedUrl = url;
  }

  void _setStatus(UpdateStatus newStatus) {
    _status = newStatus;
    statusNotifier.value = newStatus;
  }

  void dispose() {
    _checkTimer?.cancel();
    statusNotifier.dispose();
    downloadProgress.dispose();
    updateVersion.dispose();
    updateError.dispose();
  }
}
