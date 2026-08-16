enum IdentityState {
  unknown,
  loading,
  unauthenticated,
  verifying,
  pending,
  authenticated,
  workspaceRequired,
  authorized,
  sessionExpired,
  suspended,
  locked,
  error,
}

class IdentityError {
  final String code;
  final String message;
  final int? statusCode;
  final bool retryable;
  final bool reauthenticate;

  const IdentityError({
    required this.code,
    required this.message,
    this.statusCode,
    this.retryable = false,
    this.reauthenticate = false,
  });
}

IdentityState identityStateFor({
  required bool hasUser,
  required bool hasWorkspaceContext,
  required bool hasWorkspaces,
}) {
  if (!hasUser) return IdentityState.unauthenticated;
  if (!hasWorkspaces) return IdentityState.authenticated;
  if (!hasWorkspaceContext) return IdentityState.workspaceRequired;
  return IdentityState.authorized;
}
