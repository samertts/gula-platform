import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { getCurrentUser, logout as authLogout } from '../services/auth';
import type { CitizenUser } from '../types';

interface AuthContextValue {
  user: CitizenUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (user: CitizenUser) => void;
  logout: () => void;
  updateUser: (updates: Partial<CitizenUser>) => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CitizenUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initAuth();
  }, []);

  async function initAuth() {
    try {
      const currentUser = await getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  const login = useCallback((userData: CitizenUser) => {
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    authLogout();
    setUser(null);
  }, []);

  const updateUser = useCallback((updates: Partial<CitizenUser>) => {
    setUser((prev) => {
      if (!prev) return prev;
      return { ...prev, ...updates };
    });
  }, []);

  const refreshAuth = useCallback(async () => {
    const currentUser = await getCurrentUser();
    setUser(currentUser);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        updateUser,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
