import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../api/api_endpoints.dart';
import '../api/api_exceptions.dart';
import 'secure_storage.dart';
import 'biometric_auth.dart';
import 'identity_state.dart';

enum AuthStatus {
  uninitialized,
  authenticated,
  unauthenticated,
  authenticating,
  mfaRequired,
  requiresSetup,
  unknown,
  loading,
  verifying,
  pending,
  workspaceRequired,
  authorized,
  sessionExpired,
  suspended,
  locked,
  error,
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
  List<Map<String, dynamic>> _memberships = const [];
  Map<String, List<String>> _effectivePermissions = const {};
  List<Map<String, dynamic>> _workspaces = const [];
  Map<String, dynamic>? _workspaceContext;
  IdentityState _identityState = IdentityState.unknown;
  IdentityError? _identityError;

  AuthStatus get status => _status;
  IdentityState get identityState => _identityState;
  IdentityError? get identityError => _identityError;
  List<Map<String, dynamic>> get workspaces => List.unmodifiable(_workspaces);
  Map<String, dynamic>? get workspaceContext =>
      _workspaceContext == null ? null : Map.unmodifiable(_workspaceContext!);
  String? get token => _token;
  String? get refreshToken => _refreshToken;
  String? get userId => _userId;
  String? get labId => _labId;
  String? get userRole => _userRole;
  String? get userName => _userName;
  String? get userEmail => _userEmail;
  Map<String, dynamic>? get userProfile => _userProfile;
  List<Map<String, dynamic>> get memberships => List.unmodifiable(_memberships);
  Map<String, List<String>> get effectivePermissions =>
      Map.unmodifiable(_effectivePermissions);
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get isMfaRequired => _status == AuthStatus.mfaRequired;
  BiometricAuth get biometricAuth => _biometricAuth;
  ApiClient get apiClient => _apiClient;

  final ValueNotifier<AuthStatus> statusNotifier = ValueNotifier(
    AuthStatus.uninitialized,
  );
  final ValueNotifier<IdentityState> identityStateNotifier = ValueNotifier(
    IdentityState.unknown,
  );
  final ValueNotifier<String?> errorNotifier = ValueNotifier(null);

  Future<void> initialize({required String apiUrl}) async {
    _setIdentityState(IdentityState.loading);
    await _biometricAuth.initialize();
    await _storage.saveApiUrl(apiUrl);

    _apiClient = ApiClient(
      baseUrl: apiUrl,
      getToken: () => _token ?? '',
      getRefreshToken: () => _refreshToken ?? '',
      onRefreshToken: _refreshAccessToken,
      onAuthFailure: () => _markSessionExpired(),
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
      await _refreshWorkspaceContext();
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
        _setIdentityError(error);
        rethrow;
      }
      errorNotifier.value = 'Login failed. Please try again.';
      _setIdentityError(e);
      rethrow;
    } catch (e) {
      errorNotifier.value = 'Login failed. Please try again.';
      _setIdentityError(e);
      _setStatus(AuthStatus.unauthenticated);
      rethrow;
    }
  }

  String? _mfaSessionToken;
  Future<bool>? _refreshInFlight;

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
        _setIdentityError(error);
      } else {
        _setIdentityError(e);
      }
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> refreshWorkspaces() async {
    final response = await _apiClient.get(ApiEndpoints.workspaces);
    final body = response.data;
    final raw = body is Map<String, dynamic>
        ? (body['workspaces'] ?? body['items'])
        : body;
    _workspaces = raw is List
        ? raw
              .whereType<Map>()
              .map((item) => Map<String, dynamic>.from(item))
              .toList(growable: false)
        : const [];
    _setIdentityState(
      identityStateFor(
        hasUser: _userId != null,
        hasWorkspaceContext: _workspaceContext != null,
        hasWorkspaces: _workspaces.isNotEmpty,
      ),
    );
    return workspaces;
  }

  Future<Map<String, dynamic>> switchWorkspace(String workspaceId) async {
    final response = await _apiClient.post(
      ApiEndpoints.switchWorkspace(workspaceId),
      data: {},
    );
    final body = response.data;
    if (body is! Map<String, dynamic>)
      throw StateError('Invalid workspace context response.');
    _workspaceContext = body['context'] is Map<String, dynamic>
        ? Map<String, dynamic>.from(body['context'] as Map<String, dynamic>)
        : Map<String, dynamic>.from(body);
    _setIdentityState(IdentityState.authorized);
    await refreshMemberships();
    return Map.unmodifiable(_workspaceContext!);
  }

  Future<void> _refreshWorkspaceContext() async {
    try {
      await refreshWorkspaces();
    } catch (_) {
      _workspaces = const [];
    }
    // No client-side auto-selection. A server-approved context is required.
    if (_workspaceContext == null &&
        _userId != null &&
        _workspaces.isNotEmpty) {
      _setIdentityState(IdentityState.workspaceRequired);
    }
  }

  Future<List<Map<String, dynamic>>> refreshMemberships() async {
    final response = await _apiClient.get(ApiEndpoints.myMemberships);
    final body = response.data;
    final rawMemberships = body is Map<String, dynamic>
        ? body['memberships']
        : null;
    final parsed = rawMemberships is List
        ? rawMemberships
              .whereType<Map>()
              .map((item) => Map<String, dynamic>.from(item))
              .toList(growable: false)
        : const <Map<String, dynamic>>[];
    _memberships = parsed;
    await refreshEffectivePermissions();
    return memberships;
  }

  Future<Map<String, List<String>>> refreshEffectivePermissions() async {
    final reflected = <String, List<String>>{};
    final organizationIds = _memberships
        .map((membership) => membership['organization_id']?.toString())
        .whereType<String>()
        .toSet();
    for (final organizationId in organizationIds) {
      try {
        final response = await _apiClient.get(
          ApiEndpoints.effectivePermissions,
          queryParameters: {'organization_id': organizationId},
        );
        final body = response.data;
        final data = body is Map<String, dynamic> ? body['permissions'] : null;
        reflected[organizationId] = data is List
            ? data.whereType<String>().toList(growable: false)
            : const <String>[];
      } catch (_) {
        reflected[organizationId] = const <String>[];
      }
    }
    _effectivePermissions = reflected;
    return effectivePermissions;
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

    // Memberships and capabilities are server-reflected UX context,
    // never an offline authorization cache or security decision.
    try {
      await refreshMemberships();
    } catch (_) {
      _memberships = const [];
      _effectivePermissions = const {};
    }
    await _refreshWorkspaceContext();
    _setStatus(AuthStatus.authenticated);
  }

  Future<bool> _refreshAccessToken() {
    final inFlight = _refreshInFlight;
    if (inFlight != null) return inFlight;
    if (_refreshToken == null || _refreshToken!.isEmpty)
      return Future.value(false);
    final future = _performRefresh();
    _refreshInFlight = future;
    return future.whenComplete(() => _refreshInFlight = null);
  }

  Future<bool> _performRefresh() async {
    try {
      final response = await apiClient.post(
        ApiEndpoints.refreshToken,
        data: {'refresh_token': _refreshToken},
        options: Options(extra: {'skipAuthRefresh': true}),
      );
      final data = response.data as Map<String, dynamic>;
      _token = (data['access_token'] ?? data['token']) as String?;
      _refreshToken = data['refresh_token'] as String?;
      if (_token != null) await _storage.saveToken(_token!);
      if (_refreshToken != null)
        await _storage.saveRefreshToken(_refreshToken!);
      return _token != null;
    } catch (_) {
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
    _memberships = const [];
    _effectivePermissions = const {};
    _workspaces = const [];
    _workspaceContext = null;
    _identityError = null;
    await _storage.clear();
    _setIdentityState(IdentityState.unauthenticated);
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
    _syncIdentityState(newStatus);
  }

  void _syncIdentityState(AuthStatus status) {
    final mapped = switch (status) {
      AuthStatus.uninitialized => IdentityState.unknown,
      AuthStatus.authenticating => IdentityState.verifying,
      AuthStatus.mfaRequired => IdentityState.verifying,
      AuthStatus.requiresSetup => IdentityState.pending,
      AuthStatus.authenticated => identityStateFor(
        hasUser: _userId != null,
        hasWorkspaceContext: _workspaceContext != null,
        hasWorkspaces: _workspaces.isNotEmpty,
      ),
      AuthStatus.authorized => IdentityState.authorized,
      AuthStatus.workspaceRequired => IdentityState.workspaceRequired,
      AuthStatus.sessionExpired => IdentityState.sessionExpired,
      AuthStatus.suspended => IdentityState.suspended,
      AuthStatus.locked => IdentityState.locked,
      AuthStatus.error => IdentityState.error,
      AuthStatus.unknown => IdentityState.unknown,
      AuthStatus.loading => IdentityState.loading,
      AuthStatus.verifying => IdentityState.verifying,
      AuthStatus.pending => IdentityState.pending,
      AuthStatus.unauthenticated => IdentityState.unauthenticated,
    };
    _setIdentityState(mapped);
  }

  void _setIdentityState(IdentityState state) {
    _identityState = state;
    identityStateNotifier.value = state;
  }

  void _setIdentityError(Object error) {
    final apiError = error is ApiException ? error : null;
    final statusCode = apiError?.statusCode;
    final state = statusCode == 423
        ? IdentityState.locked
        : statusCode == 403
        ? IdentityState.suspended
        : IdentityState.error;
    _identityError = IdentityError(
      code: statusCode == 423
          ? 'LOCKED'
          : statusCode == 403
          ? 'SUSPENDED'
          : 'REQUEST_FAILED',
      message: statusCode == 401
          ? 'Invalid credentials or expired session.'
          : apiError?.message ?? 'The request could not be completed.',
      statusCode: statusCode,
      retryable: statusCode == null || statusCode >= 500 || statusCode == 429,
      reauthenticate: statusCode == 401,
    );
    _setIdentityState(state);
  }

  void _markSessionExpired() {
    _identityError = const IdentityError(
      code: 'SESSION_EXPIRED',
      message: 'Your session has expired. Please sign in again.',
      statusCode: 401,
      reauthenticate: true,
    );
    _setIdentityState(IdentityState.sessionExpired);
    _status = AuthStatus.sessionExpired;
    statusNotifier.value = _status;
  }

  void dispose() {
    statusNotifier.dispose();
    identityStateNotifier.dispose();
    errorNotifier.dispose();
    _apiClient.dispose();
  }
}
