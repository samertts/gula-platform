import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../api/api_endpoints.dart';
import '../api/api_exceptions.dart';
import 'secure_storage.dart';
import 'biometric_auth.dart';

enum AuthStatus {
  uninitialized,
  authenticated,
  unauthenticated,
  authenticating,
  mfaRequired,
  requiresSetup,
}

class AuthManager {
  final SecureStorage _storage = SecureStorage();
  final BiometricAuth _biometricAuth = BiometricAuth();

  late final ApiClient _apiClient;

  AuthStatus _status = AuthStatus.uninitialized;
  String? _token;
  String? _refreshToken;
  String? _userId;
  String? _labId;
  String? _userRole;
  String? _userName;
  String? _userEmail;
  Map<String, dynamic>? _userProfile;

  AuthStatus get status => _status;
  String? get token => _token;
  String? get refreshToken => _refreshToken;
  String? get userId => _userId;
  String? get labId => _labId;
  String? get userRole => _userRole;
  String? get userName => _userName;
  String? get userEmail => _userEmail;
  Map<String, dynamic>? get userProfile => _userProfile;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get isMfaRequired => _status == AuthStatus.mfaRequired;
  BiometricAuth get biometricAuth => _biometricAuth;
  ApiClient get apiClient => _apiClient;

  final ValueNotifier<AuthStatus> statusNotifier = ValueNotifier(
    AuthStatus.uninitialized,
  );
  final ValueNotifier<String?> errorNotifier = ValueNotifier(null);

  Future<void> initialize({required String apiUrl}) async {
    await _biometricAuth.initialize();
    await _storage.saveApiUrl(apiUrl);

    _apiClient = ApiClient(
      baseUrl: apiUrl,
      getToken: () => _token ?? '',
      getRefreshToken: () => _refreshToken ?? '',
      onRefreshToken: _refreshAccessToken,
      onAuthFailure: () => _setStatus(AuthStatus.unauthenticated),
      enableLogging: kDebugMode,
    );

    final savedToken = await _storage.getToken();
    final savedRefreshToken = await _storage.getRefreshToken();
    if (savedToken != null && savedToken.isNotEmpty) {
      _token = savedToken;
      _refreshToken = savedRefreshToken;
      _userId = await _storage.getUserId();
      _labId = await _storage.getLabId();
      _userRole = await _storage.getUserRole();
      try {
        await _validateToken();
      } catch (_) {
        final refreshed = await _refreshAccessToken();
        if (!refreshed) {
          await logout();
          return;
        }
      }
      _setStatus(AuthStatus.authenticated);
    } else {
      _setStatus(AuthStatus.unauthenticated);
    }
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    _setStatus(AuthStatus.authenticating);
    errorNotifier.value = null;

    try {
      final response = await _apiClient.post(
        ApiEndpoints.login,
        data: {'email': email, 'password': password},
        idempotent: true,
      );

      final data = response.data as Map<String, dynamic>;

      if (data.containsKey('mfa_required') && data['mfa_required'] == true) {
        _mfaSessionToken = data['session_token'] as String?;
        _setStatus(AuthStatus.mfaRequired);
        return data;
      }

      await _processLoginResponse(data);
      return data;
    } on DioException catch (e) {
      final error = e.error;
      if (error is ApiException) {
        errorNotifier.value = error.message;
        rethrow;
      }
      errorNotifier.value = 'Login failed. Please try again.';
      rethrow;
    } catch (e) {
      errorNotifier.value = 'Login failed. Please try again.';
      _setStatus(AuthStatus.unauthenticated);
      rethrow;
    }
  }

  String? _mfaSessionToken;

  Future<Map<String, dynamic>> verifyMfa({
    required String code,
    required String method,
  }) async {
    errorNotifier.value = null;
    try {
      final response = await _apiClient.post(
        ApiEndpoints.verifyMfa,
        data: {
          'code': code,
          'method': method,
          'session_token': _mfaSessionToken,
        },
      );
      final data = response.data as Map<String, dynamic>;
      await _processLoginResponse(data);
      return data;
    } on DioException catch (e) {
      final error = e.error;
      if (error is ApiException) {
        errorNotifier.value = error.message;
      }
      rethrow;
    }
  }

  Future<void> _processLoginResponse(Map<String, dynamic> data) async {
    final user = (data['user'] is Map<String, dynamic>)
        ? data['user'] as Map<String, dynamic>
        : data;
    _token = (data['access_token'] ?? data['token']) as String?;
    _refreshToken = data['refresh_token'] as String?;
    _userId = (user['id'] ?? data['user_id'])?.toString();
    _labId = (user['lab_id'] ?? data['lab_id'])?.toString();
    _userRole = (user['role'] ?? data['role']) as String?;
    _userName = (user['name'] ?? user['full_name'] ?? data['name']) as String?;
    _userEmail = (user['email'] ?? data['email']) as String?;
    _userProfile =
        (user['profile'] ?? data['profile']) as Map<String, dynamic>?;

    if (_token != null) {
      await _storage.saveToken(_token!);
    }
    if (_refreshToken != null) {
      await _storage.saveRefreshToken(_refreshToken!);
    }
    if (_userId != null) await _storage.saveUserId(_userId!);
    if (_labId != null) await _storage.saveLabId(_labId!);
    if (_userRole != null) await _storage.saveUserRole(_userRole!);

    _setStatus(AuthStatus.authenticated);
  }

  Future<bool> _refreshAccessToken() async {
    if (_refreshToken == null || _refreshToken!.isEmpty) return false;
    try {
      final response = await apiClient.post(
        ApiEndpoints.refreshToken,
        data: {'refresh_token': _refreshToken},
      );
      final data = response.data as Map<String, dynamic>;
      _token = (data['access_token'] ?? data['token']) as String?;
      _refreshToken = data['refresh_token'] as String?;
      if (_token != null) await _storage.saveToken(_token!);
      if (_refreshToken != null)
        await _storage.saveRefreshToken(_refreshToken!);
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<void> _validateToken() async {
    try {
      await _apiClient.get(ApiEndpoints.session);
    } catch (_) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> startDemo() async {
    _setStatus(AuthStatus.authenticating);
    try {
      final response = await _apiClient.post(ApiEndpoints.demoAccess);
      final data = response.data as Map<String, dynamic>;
      await _processLoginResponse(data);
      return data;
    } catch (_) {
      _setStatus(AuthStatus.unauthenticated);
      rethrow;
    }
  }

  Future<void> logout() async {
    try {
      await _apiClient.post(ApiEndpoints.logout);
    } catch (_) {}
    _token = null;
    _refreshToken = null;
    _userId = null;
    _labId = null;
    _userRole = null;
    _userName = null;
    _userEmail = null;
    _userProfile = null;
    await _storage.clear();
    _setStatus(AuthStatus.unauthenticated);
  }

  Future<bool> authenticateWithBiometric() async {
    if (!_biometricAuth.isAvailable) return false;
    final authenticated = await _biometricAuth.authenticate();
    if (authenticated) {
      await initialize(apiUrl: await _storage.getApiUrl() ?? '');
      return status == AuthStatus.authenticated;
    }
    return false;
  }

  Future<void> enableBiometric() async {
    await _storage.saveBiometricEnabled(true);
  }

  Future<void> disableBiometric() async {
    await _storage.saveBiometricEnabled(false);
  }

  Future<bool> isBiometricEnabled() => _storage.isBiometricEnabled();

  void _setStatus(AuthStatus newStatus) {
    _status = newStatus;
    statusNotifier.value = newStatus;
  }

  void dispose() {
    statusNotifier.dispose();
    errorNotifier.dispose();
    _apiClient.dispose();
  }
}
