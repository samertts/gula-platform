import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { UserInfo, LoginRequest } from "@/types";
import { authApi } from "@/api/endpoints";
import { setApiMode } from "@/api/client";

interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  demoMode: boolean;
  login: (data: LoginRequest) => Promise<void>;
  startDemo: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);
const DEMO_SESSION_KEY = "gula_demo_active";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    let mounted = true;

    const restoreSession = async () => {
      const hasDemoMarker = window.sessionStorage.getItem(DEMO_SESSION_KEY) === "true";
      try {
        const session = await authApi.session();
        if (hasDemoMarker && !session.demo_mode) {
          throw new Error("Demo marker exists but the server session is not a demo session");
        }
        if (mounted) {
          setUser(session.user);
          setDemoMode(Boolean(session.demo_mode));
        }
      } catch {
        window.sessionStorage.removeItem(DEMO_SESSION_KEY);
        setApiMode("live");
        if (mounted) {
          setUser(null);
          setDemoMode(false);
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
  };

  const startDemo = async () => {
    const res = await authApi.demoAccess();
    window.sessionStorage.setItem(DEMO_SESSION_KEY, "true");
    setUser(res.user);
    setDemoMode(true);
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
      setApiMode("live");
      setUser(null);
      setDemoMode(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        demoMode,
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
