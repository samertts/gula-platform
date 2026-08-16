import type { UserInfo } from "@/types";
import type { MembershipSummary, WorkspaceContextResponse, WorkspaceSummary } from "@/api/client";

export const AUTH_STATES = {
  UNKNOWN: "UNKNOWN",
  LOADING: "LOADING",
  UNAUTHENTICATED: "UNAUTHENTICATED",
  VERIFYING: "VERIFYING",
  PENDING: "PENDING",
  AUTHENTICATED: "AUTHENTICATED",
  WORKSPACE_REQUIRED: "WORKSPACE_REQUIRED",
  AUTHORIZED: "AUTHORIZED",
  SESSION_EXPIRED: "SESSION_EXPIRED",
  SUSPENDED: "SUSPENDED",
  LOCKED: "LOCKED",
  ERROR: "ERROR",
} as const;

export type AuthState = typeof AUTH_STATES[keyof typeof AUTH_STATES];

export interface AuthStateError {
  code: string;
  status?: number;
  message: string;
  retryable?: boolean;
  reauthenticate?: boolean;
}

export interface AuthSnapshot {
  state: AuthState;
  user: UserInfo | null;
  memberships: MembershipSummary[];
  effectivePermissions: Record<string, string[]>;
  workspace: WorkspaceSummary | null;
  workspaceContext: WorkspaceContextResponse["context"] | null;
  error: AuthStateError | null;
  demoMode: boolean;
}

export function isAuthenticatedState(state: AuthState): boolean {
  return state === AUTH_STATES.AUTHENTICATED || state === AUTH_STATES.WORKSPACE_REQUIRED || state === AUTH_STATES.AUTHORIZED;
}

export function isSessionTerminalState(state: AuthState): boolean {
  return state === AUTH_STATES.UNAUTHENTICATED || state === AUTH_STATES.SESSION_EXPIRED || state === AUTH_STATES.SUSPENDED || state === AUTH_STATES.LOCKED;
}

export function stateForAuthorizedContext(
  user: UserInfo,
  workspaces: WorkspaceSummary[],
  activeWorkspace: WorkspaceSummary | null,
): AuthState {
  if (!user) return AUTH_STATES.UNAUTHENTICATED;
  if (workspaces.length === 0) return AUTH_STATES.AUTHENTICATED;
  if (activeWorkspace) return AUTH_STATES.AUTHORIZED;
  return AUTH_STATES.WORKSPACE_REQUIRED;
}
