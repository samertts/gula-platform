import 'package:flutter/foundation.dart';

import 'auth_manager.dart';
import 'biometric_auth.dart';

class AuthProvider extends ChangeNotifier {
  final AuthManager _authManager;

  AuthProvider(this._authManager) {
    _authManager.statusNotifier.addListener(_onStatusChanged);
  }

  AuthManager get manager => _authManager;
  BiometricAuth get biometric => _authManager.biometricAuth;

  bool get isAuthenticated => _authManager.isAuthenticated;
  bool get isMfaRequired => _authManager.isMfaRequired;
  bool get isLoading => _authManager.status == AuthStatus.authenticating;
  bool get isInitialized => _authManager.status != AuthStatus.uninitialized;

  String? get error => _authManager.errorNotifier.value;
  String? get token => _authManager.token;
  String? get userId => _authManager.userId;
  String? get labId => _authManager.labId;
  String? get userRole => _authManager.userRole;
  String? get userName => _authManager.userName;
  String? get userEmail => _authManager.userEmail;

  Future<void> initialize({required String apiUrl}) async {
    await _authManager.initialize(apiUrl: apiUrl);
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final result = await _authManager.login(email: email, password: password);
    notifyListeners();
    return result;
  }

  Future<Map<String, dynamic>> verifyMfa({
    required String code,
    required String method,
  }) async {
    final result = await _authManager.verifyMfa(code: code, method: method);
    notifyListeners();
    return result;
  }

  Future<Map<String, dynamic>> startDemo() async {
    final result = await _authManager.startDemo();
    notifyListeners();
    return result;
  }

  Future<void> logout() async {
    await _authManager.logout();
    notifyListeners();
  }

  Future<bool> authenticateWithBiometric() async {
    final result = await _authManager.authenticateWithBiometric();
    if (result) notifyListeners();
    return result;
  }

  Future<void> enableBiometric() async {
    await _authManager.enableBiometric();
    notifyListeners();
  }

  Future<void> disableBiometric() async {
    await _authManager.disableBiometric();
    notifyListeners();
  }

  Future<bool> isBiometricEnabled() => _authManager.isBiometricEnabled();

  void _onStatusChanged() {
    notifyListeners();
  }

  @override
  void dispose() {
    _authManager.statusNotifier.removeListener(_onStatusChanged);
    super.dispose();
  }
}
