import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureConfig {
  SecureConfig._();

  static const FlutterSecureStorage _storage = FlutterSecureStorage();

  static const _keyApiUrl = 'api_url';
  static const _keyToken = 'auth_token';
  static const _keyRefreshToken = 'refresh_token';
  static const _keyUserId = 'user_id';
  static const _keyLabId = 'lab_id';
  static const _keyUserRole = 'user_role';
  static const _keyThemeMode = 'theme_mode';
  static const _keyLocale = 'locale';
  static const _keyBiometricEnabled = 'biometric_enabled';
  static const _keyDeviceId = 'device_id';
  static const _keyLastSync = 'last_sync_timestamp';
  static const _keyEncryptionKey = 'encryption_key';

  static AndroidOptions _androidOptions() => const AndroidOptions(
        encryptedSharedPreferences: true,
        accessibility: KeychainAccessibility.passcode,
      );

  static IOSOptions _iosOptions() => const IOSOptions(
        accessibility: KeychainAccessibility.passcode,
        authenticationType: BiometricType.biometricAny,
      );

  static const _defaultOptions = _DefaultOptions();

  static Future<void> write(String key, String value) async {
    await _storage.write(key: key, value: value, aOptions: _androidOptions(), iOptions: _iosOptions());
  }

  static Future<String?> read(String key) async {
    return await _storage.read(key: key, aOptions: _androidOptions(), iOptions: _iosOptions());
  }

  static Future<void> delete(String key) async {
    await _storage.delete(key: key, aOptions: _androidOptions(), iOptions: _iosOptions());
  }

  static Future<void> clear() async {
    await _storage.deleteAll(aOptions: _androidOptions(), iOptions: _iosOptions());
  }

  static Future<void> setApiUrl(String url) => write(_keyApiUrl, url);
  static Future<String?> getApiUrl() => read(_keyApiUrl);

  static Future<void> setToken(String token) => write(_keyToken, token);
  static Future<String?> getToken() => read(_keyToken);

  static Future<void> setRefreshToken(String token) => write(_keyRefreshToken, token);
  static Future<String?> getRefreshToken() => read(_keyRefreshToken);

  static Future<void> setUserId(String id) => write(_keyUserId, id);
  static Future<String?> getUserId() => read(_keyUserId);

  static Future<void> setLabId(String id) => write(_keyLabId, id);
  static Future<String?> getLabId() => read(_keyLabId);

  static Future<void> setUserRole(String role) => write(_keyUserRole, role);
  static Future<String?> getUserRole() => read(_keyUserRole);

  static Future<void> setThemeMode(String mode) => write(_keyThemeMode, mode);
  static Future<String?> getThemeMode() => read(_keyThemeMode);

  static Future<void> setLocale(String locale) => write(_keyLocale, locale);
  static Future<String?> getLocale() => read(_keyLocale);

  static Future<void> setBiometricEnabled(bool enabled) =>
      write(_keyBiometricEnabled, enabled.toString());
  static Future<bool> isBiometricEnabled() async {
    final val = await read(_keyBiometricEnabled);
    return val == 'true';
  }

  static Future<void> setDeviceId(String id) => write(_keyDeviceId, id);
  static Future<String?> getDeviceId() => read(_keyDeviceId);

  static Future<void> setLastSync(String timestamp) => write(_keyLastSync, timestamp);
  static Future<String?> getLastSync() => read(_keyLastSync);

  static Future<String> getOrCreateEncryptionKey() async {
    final existing = await read(_keyEncryptionKey);
    if (existing != null && existing.isNotEmpty) return existing;
    final key = _generateKey();
    await write(_keyEncryptionKey, key);
    return key;
  }

  static String _generateKey() {
    final bytes = List<int>.generate(32, (_) => DateTime.now().microsecondsSinceEpoch % 256);
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  }
}

class _DefaultOptions extends IOSOptions {
  const _DefaultOptions()
      : super(
          accessibility: KeychainAccessibility.passcode,
          authenticationType: BiometricType.biometricAny,
        );
}
