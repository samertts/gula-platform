import 'package:flutter_test/flutter_test.dart';

import '../../lib/core/auth/auth_manager.dart';

void main() {
  group('AuthStatus', () {
    test('defines the supported authentication lifecycle states', () {
      expect(
        AuthStatus.values,
        containsAll(<AuthStatus>[
          AuthStatus.uninitialized,
          AuthStatus.authenticated,
          AuthStatus.unauthenticated,
          AuthStatus.authenticating,
          AuthStatus.mfaRequired,
          AuthStatus.requiresSetup,
        ]),
      );
    });
  });
}
