import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { UserInfo, LoginRequest } from "@/types";
import { authApi } from "@/api/endpoints";
import { apiClient, setApiMode, type DemoPersonaId, type MembershipSummary } from "@/api/client";

interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  demoMode: boolean;
  memberships: MembershipSummary[];
  effectivePermissions: Record<string, string[]>;
  refreshMemberships: (forceLive?: boolean) => Promise<void>;
  login: (data: LoginRequest) => Promise<void>;
  startDemo: (persona?: DemoPersonaId) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);
const DEMO_SESSION_KEY = "gula_demo_active";
const DEMO_PERSONA_KEY = "gula_demo_persona";
const DEFAULT_DEMO_PERSONA: DemoPersonaId = "doctor";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [demoMode, setDemoMode] = useState(false);
  const [memberships, setMemberships] = useState<MembershipSummary[]>([]);
  const [effectivePermissions, setEffectivePermissions] = useState<Record<string, string[]>>({});

  const refreshMemberships = async (forceLive = false) => {
    if (demoMode && !forceLive) {
      setMemberships([]);
      setEffectivePermissions({});
      return;
    }
    try {
      const response = await apiClient.listMyMemberships();
      setMemberships(response.memberships);
      const organizationIds = [...new Set(response.memberships.map((membership) => membership.organization_id))];
      const reflected = await Promise.all(
        organizationIds.map(async (organizationId) => {
          try {
            const result = await apiClient.getEffectivePermissions(organizationId);
            return [organizationId, result.permissions] as const;
          } catch {
            return [organizationId, []] as const;
          }
        }),
      );
      setEffectivePermissions(Object.fromEntries(reflected));
    } catch {
      // Memberships/capabilities are server-reflected UX context, never a local authorization fallback.
      setMemberships([]);
      setEffectivePermissions({});
    }
  };

  useEffect(() => {
    let mounted = true;

    const restoreSession = async () => {
      const hasDemoMarker = window.sessionStorage.getItem(DEMO_SESSION_KEY) === "true";
      const storedPersona = (window.sessionStorage.getItem(DEMO_PERSONA_KEY) as DemoPersonaId | null) ?? DEFAULT_DEMO_PERSONA;
      try {
        const session = hasDemoMarker
          ? await authApi.demoAccess(storedPersona)
          : await authApi.session();
        if (mounted) {
          setUser(session.user);
          setDemoMode(Boolean(session.demo_mode));
          if (!session.demo_mode) void refreshMemberships(true);
          if (hasDemoMarker) window.sessionStorage.setItem(DEMO_SESSION_KEY, "true");
        }
      } catch {
        window.sessionStorage.removeItem(DEMO_SESSION_KEY);
        setApiMode("live");
        if (mounted) {
          setUser(null);
          setDemoMode(false);
          setMemberships([]);
          setEffectivePermissions({});
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    const handleSessionExpired = () => {
      window.sessionStorage.removeItem(DEMO_SESSION_KEY);
      setApiMode("live");
      if (mounted) {
        setUser(null);
        setDemoMode(false);
      }
    };

    window.addEventListener("gula:session-expired", handleSessionExpired);
    void restoreSession();
    return () => {
      mounted = false;
      window.removeEventListener("gula:session-expired", handleSessionExpired);
    };
  }, []);

  const login = async (data: LoginRequest) => {
    setApiMode("live");
    const res = await authApi.login(data);
    window.sessionStorage.removeItem(DEMO_SESSION_KEY);
    setUser(res.user);
    setDemoMode(Boolean(res.demo_mode));
    if (!res.demo_mode) await refreshMemberships(true);
  };

  const startDemo = async (persona: DemoPersonaId = DEFAULT_DEMO_PERSONA) => {
    const res = await authApi.demoAccess(persona);
    window.sessionStorage.setItem(DEMO_SESSION_KEY, "true");
    window.sessionStorage.setItem(DEMO_PERSONA_KEY, persona);
    setUser(res.user);
    setDemoMode(true);
    setMemberships([]);
    setEffectivePermissions({});
  };

  const logout = async () => {
    try {
      if (demoMode) {
        await authApi.endDemo();
      } else {
        await authApi.logout();
      }
    } finally {
      window.sessionStorage.removeItem(DEMO_SESSION_KEY);
      window.sessionStorage.removeItem(DEMO_PERSONA_KEY);
      setApiMode("live");
      setUser(null);
      setDemoMode(false);
      setMemberships([]);
      setEffectivePermissions({});
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        demoMode,
        memberships,
        effectivePermissions,
        refreshMemberships,
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
