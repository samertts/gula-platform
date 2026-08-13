import 'package:flutter/foundation.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import '../utils/constants.dart';

class CrashReporter {
  static bool _initialized = false;

  static bool get isInitialized => _initialized;

  static Future<void> initialize({
    String? dsn,
    bool enableInDebug = false,
  }) async {
    if (_initialized) return;
    if (!enableInDebug && kDebugMode) return;

    try {
      await SentryFlutter.init((options) {
        options.dsn = dsn ?? AppConstants.sentryDsn;
        options.tracesSampleRate = 0.2;
        options.enableAppHangTracking = true;
        options.enableAutoPerformanceTracing = true;
        options.enableAutoSessionTracking = true;
        options.attachScreenshot = true;
        options.attachViewHierarchy = true;
        options.maxBreadcrumbs = 100;
        options.debug = kDebugMode;
        options.environment = kDebugMode ? 'development' : 'production';
        options.reportPackages = true;
        options.sendDefaultPii = false;
        options.beforeSend = (event, hint) {
          if (kDebugMode) {
            debugPrint('[Sentry] Event: ${event.eventId}');
          }
          return event;
        };
      }, appRunner: () {});
      _initialized = true;
    } catch (e) {
      debugPrint('Sentry init error: $e');
    }
  }

  static Future<void> captureException(
    dynamic exception, {
    dynamic stackTrace,
    Map<String, dynamic>? extras,
    String? level,
  }) async {
    if (!_initialized) return;
    try {
      await Sentry.captureException(
        exception,
        stackTrace: stackTrace is StackTrace? ? stackTrace : StackTrace.current,
        withScope: (scope) {
          if (extras != null) {
            for (final entry in extras.entries) {
              scope.setExtra(entry.key, entry.value);
            }
          }
          if (level != null) {
            scope.level = SentryLevel.fromName(level);
          }
        },
      );
    } catch (e) {
      debugPrint('Sentry capture error: $e');
    }
  }

  static Future<void> captureMessage(
    String message, {
    String? level,
    Map<String, dynamic>? extras,
  }) async {
    if (!_initialized) return;
    try {
      Sentry.captureMessage(
        message,
        withScope: (scope) {
          if (extras != null) {
            for (final entry in extras.entries) {
              scope.setExtra(entry.key, entry.value);
            }
          }
          if (level != null) {
            scope.level = SentryLevel.fromName(level);
          }
        },
      );
    } catch (e) {
      debugPrint('Sentry capture error: $e');
    }
  }

  static Future<void> setUser({
    String? id,
    String? email,
    String? username,
  }) async {
    if (!_initialized) return;
    try {
      Sentry.configureScope((scope) {
        scope.setUser(SentryUser(id: id, email: email, username: username));
      });
    } catch (e) {
      debugPrint('Sentry setUser error: $e');
    }
  }

  static Future<void> removeUser() async {
    if (!_initialized) return;
    try {
      Sentry.configureScope((scope) {
        scope.setUser(null);
      });
    } catch (e) {
      debugPrint('Sentry removeUser error: $e');
    }
  }

  static Future<void> addBreadcrumb({
    required String message,
    String? category,
    String? level,
    Map<String, dynamic>? data,
  }) async {
    if (!_initialized) return;
    try {
      Sentry.addBreadcrumb(
        Breadcrumb(
          message: message,
          category: category,
          level: level != null ? SentryLevel.fromName(level) : SentryLevel.info,
          data: data,
        ),
      );
    } catch (e) {
      debugPrint('Sentry breadcrumb error: $e');
    }
  }

  static Future<void> setTag(String key, String value) async {
    if (!_initialized) return;
    try {
      Sentry.configureScope((scope) {
        scope.setTag(key, value);
      });
    } catch (e) {
      debugPrint('Sentry setTag error: $e');
    }
  }
}
