import 'dart:async';
import 'dart:io';

import 'package:auto_updater/auto_updater.dart' as updater;
import 'package:flutter/foundation.dart';

import '../utils/constants.dart';

enum UpdateStatus { idle, checking, available, downloading, readyToInstall, error, upToDate }

class AutoUpdater {
  final ValueNotifier<UpdateStatus> statusNotifier = ValueNotifier(UpdateStatus.idle);
  final ValueNotifier<double> downloadProgress = ValueNotifier(0.0);
  final ValueNotifier<String?> updateVersion = ValueNotifier(null);
  final ValueNotifier<String?> updateError = ValueNotifier(null);

  UpdateStatus _status = UpdateStatus.idle;
  bool _initialized = false;
  Timer? _checkTimer;

  bool get isInitialized => _initialized;
  UpdateStatus get status => _status;

  Future<void> initialize({
    String? feedUrl,
    int checkIntervalHours = 6,
  }) async {
    if (_initialized) return;
    _initialized = true;

    if (Platform.isWindows || Platform.isLinux) {
      try {
        if (feedUrl != null) {
          updater.AutoUpdater.feedUrl = feedUrl;
        }
        updater.AutoUpdater.onUpdateAvailable = (details) {
          updateVersion.value = details.version;
          _setStatus(UpdateStatus.available);
        };
        updater.AutoUpdater.onUpdateDownloaded = (details) {
          _setStatus(UpdateStatus.readyToInstall);
        };
        updater.AutoUpdater.onDownloadProgress = (progress) {
          downloadProgress.value = progress;
        };
        updater.AutoUpdater.onError = (error) {
          updateError.value = error.toString();
          _setStatus(UpdateStatus.error);
        };
      } catch (e) {
        debugPrint('Auto updater init error: $e');
      }
    }

    _checkTimer = Timer.periodic(
      Duration(hours: checkIntervalHours),
      (_) => checkForUpdates(),
    );
  }

  Future<bool> checkForUpdates() async {
    _setStatus(UpdateStatus.checking);
    try {
      if (Platform.isWindows || Platform.isLinux) {
        final update = await updater.AutoUpdater.checkForUpdates();
        if (update != null && update.version != AppConstants.appVersion) {
          updateVersion.value = update.version;
          _setStatus(UpdateStatus.available);
          return true;
        }
      } else if (Platform.isMacOS) {
        // macOS uses Sparkle via system update mechanism
      }
      _setStatus(UpdateStatus.upToDate);
      return false;
    } catch (e) {
      updateError.value = e.toString();
      _setStatus(UpdateStatus.error);
      return false;
    }
  }

  Future<void> downloadUpdate() async {
    _setStatus(UpdateStatus.downloading);
    try {
      if (Platform.isWindows || Platform.isLinux) {
        await updater.AutoUpdater.downloadUpdate();
      }
    } catch (e) {
      updateError.value = e.toString();
      _setStatus(UpdateStatus.error);
    }
  }

  Future<void> installUpdate() async {
    try {
      if (Platform.isWindows || Platform.isLinux) {
        await updater.AutoUpdater.installUpdate();
      }
    } catch (e) {
      updateError.value = e.toString();
      _setStatus(UpdateStatus.error);
    }
  }

  Future<void> setFeedUrl(String url) async {
    if (Platform.isWindows || Platform.isLinux) {
      updater.AutoUpdater.feedUrl = url;
    }
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
