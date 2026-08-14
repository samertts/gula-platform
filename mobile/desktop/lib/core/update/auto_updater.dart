import 'package:flutter/foundation.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/api_client.dart';

enum UpdateStatus {
  idle,
  checking,
  available,
  downloading,
  readyToInstall,
  error,
  upToDate,
}

class UpdatePolicy {
  final String platform;
  final String currentVersion;
  final String latestVersion;
  final String minimumSupportedVersion;
  final bool updateAvailable;
  final bool forceUpdate;
  final String storeUrl;
  final String message;
  final String messageAr;

  const UpdatePolicy({
    required this.platform,
    required this.currentVersion,
    required this.latestVersion,
    required this.minimumSupportedVersion,
    required this.updateAvailable,
    required this.forceUpdate,
    required this.storeUrl,
    required this.message,
    required this.messageAr,
  });

  factory UpdatePolicy.fromJson(Map<String, dynamic> json) {
    return UpdatePolicy(
      platform: json['platform'] as String? ?? 'desktop',
      currentVersion: json['current_version'] as String? ?? '0.0.0',
      latestVersion: json['latest_version'] as String? ?? '0.0.0',
      minimumSupportedVersion:
          json['minimum_supported_version'] as String? ?? '0.0.0',
      updateAvailable: json['update_available'] as bool? ?? false,
      forceUpdate: json['force_update'] as bool? ?? false,
      storeUrl:
          json['store_url'] as String? ??
          'https://github.com/samertts/gula-platform/releases',
      message: json['message'] as String? ?? 'A newer version is available.',
      messageAr: json['message_ar'] as String? ?? 'يتوفر إصدار أحدث.',
    );
  }
}

class AutoUpdater {
  final ValueNotifier<UpdateStatus> statusNotifier = ValueNotifier(
    UpdateStatus.idle,
  );
  final ValueNotifier<double> downloadProgress = ValueNotifier(0.0);
  final ValueNotifier<String?> updateVersion = ValueNotifier(null);
  final ValueNotifier<String?> updateError = ValueNotifier(null);

  UpdateStatus _status = UpdateStatus.idle;
  bool _initialized = false;
  UpdatePolicy? _policy;

  bool get isInitialized => _initialized;
  UpdateStatus get status => _status;
  UpdatePolicy? get policy => _policy;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
  }

  Future<UpdatePolicy?> checkForUpdates({
    required ApiClient apiClient,
    required String platform,
    required String currentVersion,
  }) async {
    _setStatus(UpdateStatus.checking);
    updateError.value = null;
    try {
      final response = await apiClient.get<dynamic>(
        'https://api.gula-platform.org/app-updates',
        queryParameters: {'platform': platform, 'version': currentVersion},
      );
      final data = response.data;
      final policies = data is Map ? data['policies'] : null;
      final rawPolicy = policies is Map ? policies[platform] : null;
      if (rawPolicy is! Map) {
        _policy = null;
        _setStatus(UpdateStatus.upToDate);
        return null;
      }
      final policy = UpdatePolicy.fromJson(
        Map<String, dynamic>.from(rawPolicy),
      );
      _policy = policy;
      updateVersion.value = policy.latestVersion;
      _setStatus(
        policy.updateAvailable ? UpdateStatus.available : UpdateStatus.upToDate,
      );
      return policy;
    } catch (_) {
      // A temporary manifest failure must not prevent clinical access.
      updateError.value = 'Unable to check for updates.';
      _setStatus(UpdateStatus.error);
      return null;
    }
  }

  Future<bool> openUpdate() async {
    final url = _policy?.storeUrl;
    if (url == null || url.isEmpty) return false;
    return launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
  }

  Future<void> downloadUpdate() async {
    await openUpdate();
  }

  Future<void> installUpdate() async {
    await openUpdate();
  }

  void _setStatus(UpdateStatus newStatus) {
    _status = newStatus;
    statusNotifier.value = newStatus;
  }

  void dispose() {
    statusNotifier.dispose();
    downloadProgress.dispose();
    updateVersion.dispose();
    updateError.dispose();
  }
}
