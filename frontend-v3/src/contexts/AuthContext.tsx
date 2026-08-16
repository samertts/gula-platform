import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { UserInfo, LoginRequest } from "@/types";
import { authApi } from "@/api/endpoints";
import { apiClient, setApiMode, type DemoPersonaId, type MembershipSummary, type WorkspaceSummary } from "@/api/client";
import { classifyApiError, authFailureMessage, type ApiErrorInfo } from "@/api/errorHandling";
import {
  AUTH_STATES,
  isAuthenticatedState,
  stateForAuthorizedContext,
  type AuthSnapshot,
  type AuthState,
  type AuthStateError,
} from "@/auth/authState";

interface AuthContextType extends AuthSnapshot {
  isAuthenticated: boolean;
  isLoading: boolean;
  availableWorkspaces: WorkspaceSummary[];
  refreshIdentity: () => Promise<void>;
  refreshMemberships: (forceLive?: boolean) => Promise<void>;
  refreshWorkspaces: () => Promise<WorkspaceSummary[]>;
  switchWorkspace: (workspaceId: string) => Promise<WorkspaceSummary>;
  login: (data: LoginRequest) => Promise<void>;
  startDemo: (persona?: DemoPersonaId) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);
const DEMO_SESSION_KEY = "gula_demo_active";
const DEMO_PERSONA_KEY = "gula_demo_persona";
const DEFAULT_DEMO_PERSONA: DemoPersonaId = "doctor";

function toStateError(info: ApiErrorInfo): AuthStateError {
  return {
    code: info.code,
    status: info.status,
    message: info.message,
    retryable: info.retryable,
    reauthenticate: info.reauthenticate,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(AUTH_STATES.UNKNOWN);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [memberships, setMemberships] = useState<MembershipSummary[]>([]);
  const [effectivePermissions, setEffectivePermissions] = useState<Record<string, string[]>>({});
  const [availableWorkspaces, setAvailableWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [workspace, setWorkspace] = useState<WorkspaceSummary | null>(null);
  const [workspaceContext, setWorkspaceContext] = useState<AuthSnapshot["workspaceContext"]>(null);
  const [error, setError] = useState<AuthStateError | null>(null);

  const clearIdentity = (nextState: AuthState = AUTH_STATES.UNAUTHENTICATED) => {
    setUser(null);
    setDemoMode(false);
    setMemberships([]);
    setEffectivePermissions({});
    setAvailableWorkspaces([]);
    setWorkspace(null);
    setWorkspaceContext(null);
    setState(nextState);
  };

  const refreshScopedPermissions = async (membershipList: MembershipSummary[], activeWorkspace: WorkspaceSummary | null) => {
    if (!activeWorkspace?.organization_id) {
      setEffectivePermissions({});
      return;
    }
    const organizationId = activeWorkspace.organization_id;
    if (!membershipList.some((membership) => membership.organization_id === organizationId)) {
      setEffectivePermissions({});
      return;
    }
    try {
      const result = await apiClient.getEffectivePermissions(organizationId, {
        facility_id: activeWorkspace.facility_id ?? undefined,
        department_id: activeWorkspace.department_id ?? undefined,
        workspace_id: activeWorkspace.id,
      });
      setEffectivePermissions({ [organizationId]: result.permissions });
    } catch {
      setEffectivePermissions({});
    }
  };

  const refreshMemberships = async (forceLive = false) => {
    if (demoMode && !forceLive) {
      setMemberships([]);
      setEffectivePermissions({});
      return;
    }
    const response = await apiClient.listMyMemberships();
    setMemberships(response.memberships);
    await refreshScopedPermissions(response.memberships, workspace);
  };

  const refreshWorkspaces = async () => {
    if (demoMode) {
      setAvailableWorkspaces([]);
      return [];
    }
    const response = await apiClient.listWorkspaces();
    setAvailableWorkspaces(response.workspaces);
    return response.workspaces;
  };

  const refreshIdentity = async () => {
    setState(AUTH_STATES.LOADING);
    setError(null);
    try {
      const session = await authApi.session();
      setUser(session.user);
      setDemoMode(Boolean(session.demo_mode));
      if (session.demo_mode) {
        setMemberships([]);
        setEffectivePermissions({});
        setAvailableWorkspaces([]);
        setState(AUTH_STATES.AUTHENTICATED);
        return;
      }
      const membershipResponse = await apiClient.listMyMemberships();
      setMemberships(membershipResponse.memberships);
      setEffectivePermissions({});
      const response = await apiClient.listWorkspaces();
      setAvailableWorkspaces(response.workspaces);
      setWorkspace(null);
      setWorkspaceContext(null);
      setState(stateForAuthorizedContext(session.user, response.workspaces, null));
    } catch (caught) {
      const info = classifyApiError(caught, "تعذر التحقق من الجلسة الحالية.");
      setError(toStateError(info));
      clearIdentity(info.status === 401 ? AUTH_STATES.UNAUTHENTICATED : info.kind === "OFFLINE" ? AUTH_STATES.ERROR : AUTH_STATES.UNAUTHENTICATED);
    }
  };

  useEffect(() => {
    let mounted = true;
    const restoreSession = async () => {
      const hasDemoMarker = window.sessionStorage.getItem(DEMO_SESSION_KEY) === "true";
      const storedPersona = (window.sessionStorage.getItem(DEMO_PERSONA_KEY) as DemoPersonaId | null) ?? DEFAULT_DEMO_PERSONA;
      setState(AUTH_STATES.LOADING);
      try {
        if (hasDemoMarker) {
          const session = await authApi.demoAccess(storedPersona);
          if (!mounted) return;
          setUser(session.user);
          setDemoMode(true);
          setState(AUTH_STATES.AUTHENTICATED);
        } else {
          setApiMode("live");
          await refreshIdentity();
        }
      } catch (caught) {
        if (!mounted) return;
        window.sessionStorage.removeItem(DEMO_SESSION_KEY);
        window.sessionStorage.removeItem(DEMO_PERSONA_KEY);
        setApiMode("live");
        const info = classifyApiError(caught, "تعذر استعادة الجلسة.");
        setError(toStateError(info));
        clearIdentity(info.kind === "OFFLINE" ? AUTH_STATES.ERROR : AUTH_STATES.UNAUTHENTICATED);
      }
    };

    const handleSessionExpired = () => {
      window.sessionStorage.removeItem(DEMO_SESSION_KEY);
      window.sessionStorage.removeItem(DEMO_PERSONA_KEY);
      setApiMode("live");
      setError({ code: "SESSION_EXPIRED", message: "انتهت الجلسة أو أُبطلت. أعد تسجيل الدخول للمتابعة.", reauthenticate: true });
      clearIdentity(AUTH_STATES.SESSION_EXPIRED);
    };

    const handleApiError = (event: Event) => {
      const status = (event as CustomEvent<{ status?: number }>).detail?.status;
      if (status === 401) return;
      if (status === 403) setError({ code: "FORBIDDEN", status, message: "ليس لديك صلاحية لتنفيذ هذه العملية." });
    };

    window.addEventListener("gula:session-expired", handleSessionExpired);
    window.addEventListener("gula:api-error", handleApiError);
    void restoreSession();
    return () => {
      mounted = false;
      window.removeEventListener("gula:session-expired", handleSessionExpired);
      window.removeEventListener("gula:api-error", handleApiError);
    };
    // Restore only once; the server session is the source of truth.
  }, []);

  const login = async (data: LoginRequest) => {
    setState(AUTH_STATES.VERIFYING);
    setError(null);
    setApiMode("live");
    try {
      const response = await authApi.login(data);
      window.sessionStorage.removeItem(DEMO_SESSION_KEY);
      window.sessionStorage.removeItem(DEMO_PERSONA_KEY);
      setUser(response.user);
      setDemoMode(Boolean(response.demo_mode));
      if (response.demo_mode) {
        setState(AUTH_STATES.AUTHENTICATED);
        return;
      }
      const membershipResponse = await apiClient.listMyMemberships();
      setMemberships(membershipResponse.memberships);
      setEffectivePermissions({});
      const workspacesResponse = await apiClient.listWorkspaces();
      setAvailableWorkspaces(workspacesResponse.workspaces);
      setWorkspace(null);
      setWorkspaceContext(null);
      setState(stateForAuthorizedContext(response.user, workspacesResponse.workspaces, null));
    } catch (caught) {
      const info = authFailureMessage(caught);
      const nextState = info.code === "LOCKED"
        ? AUTH_STATES.LOCKED
        : info.code === "VERIFICATION_REQUIRED" || info.code === "MFA_REQUIRED"
          ? AUTH_STATES.VERIFYING
          : /suspend|deactivat/i.test(info.code)
            ? AUTH_STATES.SUSPENDED
            : AUTH_STATES.ERROR;
      setError(toStateError(info));
      setState(nextState);
      throw caught;
    }
  };

  const startDemo = async (persona: DemoPersonaId = DEFAULT_DEMO_PERSONA) => {
    setState(AUTH_STATES.LOADING);
    setError(null);
    const response = await authApi.demoAccess(persona);
    window.sessionStorage.setItem(DEMO_SESSION_KEY, "true");
    window.sessionStorage.setItem(DEMO_PERSONA_KEY, persona);
    setUser(response.user);
    setDemoMode(true);
    setMemberships([]);
    setEffectivePermissions({});
    setAvailableWorkspaces([]);
    setWorkspace(null);
    setWorkspaceContext(null);
    setState(AUTH_STATES.AUTHENTICATED);
  };

  const switchWorkspace = async (workspaceId: string) => {
    setError(null);
    const response = await apiClient.switchWorkspace(workspaceId);
    setWorkspace(response.workspace);
    setWorkspaceContext(response.context);
    const membershipResponse = await apiClient.listMyMemberships();
    setMemberships(membershipResponse.memberships);
    await refreshScopedPermissions(membershipResponse.memberships, response.workspace);
    if (user) setState(AUTH_STATES.AUTHORIZED);
    return response.workspace;
  };

  const logout = async () => {
    setState(AUTH_STATES.LOADING);
    try {
      if (demoMode) await authApi.endDemo();
      else await authApi.logout();
    } finally {
      window.sessionStorage.removeItem(DEMO_SESSION_KEY);
      window.sessionStorage.removeItem(DEMO_PERSONA_KEY);
      setApiMode("live");
      clearIdentity(AUTH_STATES.UNAUTHENTICATED);
      setError(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        state,
        user,
        memberships,
        effectivePermissions,
        workspace,
        workspaceContext,
        error,
        demoMode,
        isAuthenticated: isAuthenticatedState(state) && Boolean(user),
        isLoading: state === AUTH_STATES.UNKNOWN || state === AUTH_STATES.LOADING || state === AUTH_STATES.VERIFYING,
        availableWorkspaces,
        refreshIdentity,
        refreshMemberships,
        refreshWorkspaces,
        switchWorkspace,
        login,
        startDemo,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
