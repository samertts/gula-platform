import 'package:flutter_test/flutter_test.dart';

import '../../lib/core/auth/identity_state.dart';

void main() {
  test('requires explicit server workspace context', () {
    expect(identityStateFor(hasUser: true, hasWorkspaceContext: false, hasWorkspaces: true), IdentityState.workspaceRequired);
    expect(identityStateFor(hasUser: true, hasWorkspaceContext: true, hasWorkspaces: true), IdentityState.authorized);
  });

  test('keeps authenticated state without an eligible workspace', () {
    expect(identityStateFor(hasUser: true, hasWorkspaceContext: false, hasWorkspaces: false), IdentityState.authenticated);
  });

  test('exposes the complete cross-platform lifecycle states', () {
    expect(IdentityState.values, containsAll([
      IdentityState.unknown,
      IdentityState.loading,
      IdentityState.unauthenticated,
      IdentityState.verifying,
      IdentityState.pending,
      IdentityState.authenticated,
      IdentityState.workspaceRequired,
      IdentityState.authorized,
      IdentityState.sessionExpired,
      IdentityState.suspended,
      IdentityState.locked,
      IdentityState.error,
    ]));
  });
}
