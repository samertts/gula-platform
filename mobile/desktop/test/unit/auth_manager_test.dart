import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import '../../lib/core/auth/auth_manager.dart';
import '../../lib/core/auth/secure_storage.dart';
import '../../lib/core/api/api_exceptions.dart';
import '../../lib/core/api/api_endpoints.dart';

import 'auth_manager_test.mocks.dart';

@GenerateMocks([SecureStorage])
void main() {
  late MockSecureStorage mockStorage;
  late AuthManager authManager;

  setUp(() {
    mockStorage = MockSecureStorage();
    authManager = AuthManager(storage: mockStorage);
  });

  group('AuthManager', () {
    test('initial state is unauthenticated', () {
      expect(authManager.isAuthenticated, false);
      expect(authManager.isLoading, false);
      expect(authManager.currentUser, isNull);
    });

    test('login sets authenticated state on success', () async {
      when(mockStorage.write(any, any)).thenAnswer((_) async => null);

      await authManager.login(
        email: 'admin@gula.iq',
        password: 'Pass1234!',
        onApiCall: (email, password) async {
          return {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'user': {'id': '1', 'email': email, 'full_name': 'Admin', 'role': 'masterAdmin', 'lab_id': '1'},
            'requires_mfa': false,
          };
        },
      );

      expect(authManager.isAuthenticated, true);
      expect(authManager.currentUser?['email'], 'admin@gula.iq');
    });

    test('login throws AuthException on invalid credentials', () async {
      await expectLater(
        authManager.login(
          email: 'bad@gula.iq',
          password: 'wrong',
          onApiCall: (email, password) async {
            throw ApiException('Invalid credentials', statusCode: 401);
          },
        ),
        throwsA(isA<ApiException>()),
      );

      expect(authManager.isAuthenticated, false);
    });

    test('logout clears state', () async {
      when(mockStorage.write(any, any)).thenAnswer((_) async => null);
      when(mockStorage.delete(any)).thenAnswer((_) async => null);
      when(mockStorage.read(any)).thenAnswer((_) async => null);

      await authManager.login(
        email: 'admin@gula.iq',
        password: 'Pass1234!',
        onApiCall: (email, password) async {
          return {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'user': {'id': '1', 'email': email, 'full_name': 'Admin', 'role': 'masterAdmin', 'lab_id': '1'},
            'requires_mfa': false,
          };
        },
      );

      await authManager.logout();
      expect(authManager.isAuthenticated, false);
      expect(authManager.currentUser, isNull);
    });
  });
}
