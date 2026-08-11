import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { UserInfo, LoginRequest } from "@/types";
import { authApi } from "@/api/endpoints";

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    let mounted = true;
    const restoreSession = async () => {
      try {
        const session = await authApi.session();
        if (mounted) {
          setUser(session.user);
          setDemoMode(session.demo_mode);
        }
      } catch {
        if (mounted) setUser(null);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    const handleSessionExpired = () => {
      if (mounted) setUser(null);
    };

    window.addEventListener("gula:session-expired", handleSessionExpired);
    void restoreSession();
    return () => {
      mounted = false;
      window.removeEventListener("gula:session-expired", handleSessionExpired);
    };
  }, []);

  const login = async (data: LoginRequest) => {
    const res = await authApi.login(data);
    setUser(res.user);
    setDemoMode(Boolean(res.demo_mode));
  };

  const startDemo = async () => {
    const res = await authApi.demoAccess();
    setUser(res.user);
    setDemoMode(true);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
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
