import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { UserInfo, LoginRequest, LoginResponse } from "@/types";
import { authApi } from "@/api/endpoints";

interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  loginWithMfa: (mfaSession: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem("user");
      }
    }
    setIsLoading(false);
  }, []);

  const applySession = (res: LoginResponse) => {
    localStorage.setItem("access_token", res.token);
    localStorage.setItem("refresh_token", res.refresh_token);
    localStorage.setItem("user", JSON.stringify(res.user));
    setUser(res.user);
  };

  const login = async (data: LoginRequest) => {
    const res = await authApi.login(data);
    if (res && "mfa_pending" in res && res.mfa_pending) {
      throw new MFAChallengeRequired(res.mfa_session);
    }
    applySession(res as LoginResponse);
  };

  const loginWithMfa = async (mfaSession: string, code: string) => {
    applySession(await authApi.mfaVerify(mfaSession, code));
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, login, loginWithMfa, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export class MFAChallengeRequired extends Error {
  mfaSession: string;
  constructor(mfaSession: string) {
    super("MFA challenge required");
    this.mfaSession = mfaSession;
  }
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
