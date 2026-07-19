import 'package:flutter/foundation.dart';
import 'package:local_auth/local_auth.dart';
import 'package:local_auth/error_codes.dart' as auth_error;

class BiometricAuth {
  final LocalAuthentication _localAuth = LocalAuthentication();

  bool _isAvailable = false;
  bool _isSupported = false;

  bool get isAvailable => _isAvailable;
  bool get isSupported => _isSupported;

  Future<void> initialize() async {
    try {
      _isAvailable = await _localAuth.canCheckBiometrics;
      _isSupported = await _localAuth.isDeviceSupported();
    } catch (e) {
      debugPrint('BiometricAuth init error: $e');
      _isAvailable = false;
      _isSupported = false;
    }
  }

  Future<List<BiometricType>> getAvailableBiometrics() async {
    try {
      return await _localAuth.getAvailableBiometrics();
    } catch (e) {
      debugPrint('getAvailableBiometrics error: $e');
      return [];
    }
  }

  Future<bool> authenticate({
    String reason = 'Authenticate to access GULA Platform',
    String cancelButton = 'Cancel',
    String? localizedReason,
    bool useErrorDialogs = true,
    bool stickyAuth = true,
  }) async {
    try {
      return await _localAuth.authenticate(
        localizedReason: localizedReason ?? reason,
        options: AuthenticationOptions(
          biometricOnly: false,
          useErrorDialogs: useErrorDialogs,
          stickyAuth: stickyAuth,
        ),
      );
    } on Exception catch (e) {
      final errorString = e.toString();
      if (errorString.contains(auth_error.notAvailable) ||
          errorString.contains(auth_error.notEnrolled)) {
        return false;
      }
      debugPrint('BiometricAuth.authenticate error: $e');
      return false;
    }
  }

  Future<bool> authenticateWithBiometrics({
    String reason = 'Authenticate with biometrics',
  }) async {
    try {
      return await _localAuth.authenticate(
        localizedReason: reason,
        options: const AuthenticationOptions(
          biometricOnly: true,
          useErrorDialogs: true,
          stickyAuth: true,
        ),
      );
    } catch (e) {
      debugPrint('BiometricAuth.authenticateWithBiometrics error: $e');
      return false;
    }
  }

  void stopAuthentication() {
    _localAuth.stopAuthentication();
  }
}
