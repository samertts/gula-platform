import 'dart:io';

import 'package:package_info_plus/package_info_plus.dart';

class TamperDetection {
  TamperDetection._();

  static bool _isJailbrokenOrRooted = false;
  static bool _isDebugMode = false;
  static bool _isEmulator = false;
  static bool _isTampered = false;

  static bool get isJailbrokenOrRooted => _isJailbrokenOrRooted;
  static bool get isDebugMode => _isDebugMode;
  static bool get isEmulator => _isEmulator;
  static bool get isTampered => _isTampered;
  static bool get isSecure => !_isTampered && !_isJailbrokenOrRooted;

  static Future<void> initialize() async {
    await Future.wait([
      _checkJailbreakRoot(),
      _checkDebugMode(),
      _checkEmulator(),
      _checkSignature(),
    ]);
    _isTampered = _isJailbrokenOrRooted || _isDebugMode || _isEmulator;
  }

  static Future<void> _checkJailbreakRoot() async {
    _isJailbrokenOrRooted = false;
    if (Platform.isAndroid) {
      final paths = [
        '/system/app/Superuser.apk',
        '/sbin/su',
        '/system/bin/su',
        '/system/xbin/su',
        '/data/local/xbin/su',
        '/data/local/bin/su',
        '/system/sd/xbin/su',
        '/system/bin/failsafe/su',
        '/data/local/su',
        '/su/bin/su',
      ];
      for (final path in paths) {
        if (await File(path).exists()) {
          _isJailbrokenOrRooted = true;
          return;
        }
      }
    } else if (Platform.isIOS) {
      final paths = [
        '/Applications/Cydia.app',
        '/Library/MobileSubstrate/MobileSubstrate.dylib',
        '/bin/bash',
        '/usr/sbin/sshd',
        '/etc/apt',
        '/private/var/lib/apt',
      ];
      for (final path in paths) {
        if (await File(path).exists()) {
          _isJailbrokenOrRooted = true;
          return;
        }
      }
    }
  }

  static Future<void> _checkDebugMode() async {
    _isDebugMode = false;
    try {
      _isDebugMode =
          Platform.environment.containsKey('FLUTTER_TEST') ||
          Platform.environment['DEBUG'] == 'true';
    } catch (_) {}
  }

  static Future<void> _checkEmulator() async {
    _isEmulator = false;
    try {
      if (Platform.isAndroid) {
        final props = [
          'ro.hardware',
          'ro.build.fingerprint',
          'ro.product.model',
        ];
        for (final prop in props) {
          try {
            final result = await Process.run('getprop', [prop]);
            final value = result.stdout.toString().toLowerCase();
            if (value.contains('emulator') ||
                value.contains('sdk') ||
                value.contains('genymotion') ||
                value.contains('nox')) {
              _isEmulator = true;
              return;
            }
          } catch (_) {}
        }
      }
    } catch (_) {}
  }

  static Future<void> _checkSignature() async {
    try {
      final info = await PackageInfo.fromPlatform();
      if (info.packageName != 'com.gula.platform.desktop') {
        _isTampered = true;
      }
    } catch (_) {
      _isTampered = true;
    }
  }
}
