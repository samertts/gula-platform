import '../security/secure_config.dart';

class SecureStorage {
  Future<void> saveToken(String token) => SecureConfig.setToken(token);
  Future<String?> getToken() => SecureConfig.getToken();
  Future<void> saveRefreshToken(String token) => SecureConfig.setRefreshToken(token);
  Future<String?> getRefreshToken() => SecureConfig.getRefreshToken();
  Future<void> saveUserId(String id) => SecureConfig.setUserId(id);
  Future<String?> getUserId() => SecureConfig.getUserId();
  Future<void> saveLabId(String id) => SecureConfig.setLabId(id);
  Future<String?> getLabId() => SecureConfig.getLabId();
  Future<void> saveUserRole(String role) => SecureConfig.setUserRole(role);
  Future<String?> getUserRole() => SecureConfig.getUserRole();
  Future<void> saveBiometricEnabled(bool enabled) => SecureConfig.setBiometricEnabled(enabled);
  Future<bool> isBiometricEnabled() => SecureConfig.isBiometricEnabled();
  Future<void> saveApiUrl(String url) => SecureConfig.setApiUrl(url);
  Future<String?> getApiUrl() => SecureConfig.getApiUrl();
  Future<void> clear() => SecureConfig.clear();
}
