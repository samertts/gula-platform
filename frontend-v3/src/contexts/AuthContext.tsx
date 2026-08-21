import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
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
  const identityGenerationRef = useRef(0);
  const permissionGenerationRef = useRef(0);
  const identityInFlightRef = useRef<Promise<void> | null>(null);
  const loginInFlightRef = useRef<Promise<void> | null>(null);
  const logoutInFlightRef = useRef<Promise<void> | null>(null);
  const workspaceSwitchInFlightRef = useRef<Promise<WorkspaceSummary> | null>(null);

  const invalidatePendingRequests = () => {
    identityGenerationRef.current += 1;
    permissionGenerationRef.current += 1;
  };

  const clearIdentity = (nextState: AuthState = AUTH_STATES.UNAUTHENTICATED, invalidate = true) => {
    if (invalidate) invalidatePendingRequests();
    setUser(null);
    setDemoMode(false);
    setMemberships([]);
    setEffectivePermissions({});
    setAvailableWorkspaces([]);
    setWorkspace(null);
    setWorkspaceContext(null);
    setState(nextState);
  };

  const refreshScopedPermissions = async (
    membershipList: MembershipSummary[],
    activeWorkspace: WorkspaceSummary | null,
    generation = permissionGenerationRef.current,
  ) => {
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
      if (generation !== permissionGenerationRef.current) return;
      setEffectivePermissions({ [organizationId]: result.permissions });
    } catch {
      if (generation === permissionGenerationRef.current) setEffectivePermissions({});
    }
  };

  const refreshMemberships = async (forceLive = false) => {
    if (demoMode && !forceLive) {
      setMemberships([]);
      setEffectivePermissions({});
      return;
    }
    const generation = ++permissionGenerationRef.current;
    const response = await apiClient.listMyMemberships();
    if (generation !== permissionGenerationRef.current) return;
    setMemberships(response.memberships);
    await refreshScopedPermissions(response.memberships, workspace, generation);
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
    if (identityInFlightRef.current) return identityInFlightRef.current;
    const generation = ++identityGenerationRef.current;
    const run = (async () => {
      setState(AUTH_STATES.LOADING);
      setError(null);
      try {
        const session = await authApi.session();
        if (generation !== identityGenerationRef.current) return;
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
        if (generation !== identityGenerationRef.current) return;
        setMemberships(membershipResponse.memberships);
        setEffectivePermissions({});
        const response = await apiClient.listWorkspaces();
        if (generation !== identityGenerationRef.current) return;
        setAvailableWorkspaces(response.workspaces);
        setWorkspace(null);
        setWorkspaceContext(null);
        setState(stateForAuthorizedContext(session.user, response.workspaces, null));
      } catch (caught) {
        if (generation !== identityGenerationRef.current) return;
        const info = classifyApiError(caught, "تعذر التحقق من الجلسة الحالية.");
        setError(toStateError(info));
        clearIdentity(info.status === 401 ? AUTH_STATES.UNAUTHENTICATED : info.kind === "OFFLINE" ? AUTH_STATES.ERROR : AUTH_STATES.UNAUTHENTICATED, false);
      }
    })().finally(() => {
      if (identityInFlightRef.current === run) identityInFlightRef.current = null;
    });
    identityInFlightRef.current = run;
    return run;
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
    if (loginInFlightRef.current) return loginInFlightRef.current;
    invalidatePendingRequests();
    setState(AUTH_STATES.VERIFYING);
    setError(null);
    setApiMode("live");
    const run = (async () => {
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
    })().finally(() => {
      if (loginInFlightRef.current === run) loginInFlightRef.current = null;
    });
    loginInFlightRef.current = run;
    return run;
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
    if (workspaceSwitchInFlightRef.current) return workspaceSwitchInFlightRef.current;
    const generation = ++permissionGenerationRef.current;
    setError(null);
    setWorkspace(null);
    setWorkspaceContext(null);
    setEffectivePermissions({});
    setState(AUTH_STATES.WORKSPACE_REQUIRED);
    const run = (async () => {
      const response = await apiClient.switchWorkspace(workspaceId);
      if (generation !== permissionGenerationRef.current) throw new Error("WORKSPACE_SWITCH_SUPERSEDED");
      setWorkspace(response.workspace);
      setWorkspaceContext(response.context);
      const membershipResponse = await apiClient.listMyMemberships();
      if (generation !== permissionGenerationRef.current) throw new Error("WORKSPACE_SWITCH_SUPERSEDED");
      setMemberships(membershipResponse.memberships);
      await refreshScopedPermissions(membershipResponse.memberships, response.workspace, generation);
      if (user && generation === permissionGenerationRef.current) setState(AUTH_STATES.AUTHORIZED);
      return response.workspace;
    })().finally(() => {
      if (workspaceSwitchInFlightRef.current === run) workspaceSwitchInFlightRef.current = null;
    });
    workspaceSwitchInFlightRef.current = run;
    return run;
  };

  const logout = async () => {
    if (logoutInFlightRef.current) return logoutInFlightRef.current;
    invalidatePendingRequests();
    setState(AUTH_STATES.LOADING);
    const run = (async () => {
      try {
        if (demoMode) await authApi.endDemo();
        else await authApi.logout();
      } finally {
        window.sessionStorage.removeItem(DEMO_SESSION_KEY);
        window.sessionStorage.removeItem(DEMO_PERSONA_KEY);
        setApiMode("live");
        clearIdentity(AUTH_STATES.UNAUTHENTICATED, false);
        setError(null);
      }
    })().finally(() => {
      if (logoutInFlightRef.current === run) logoutInFlightRef.current = null;
    });
    logoutInFlightRef.current = run;
    return run;
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
