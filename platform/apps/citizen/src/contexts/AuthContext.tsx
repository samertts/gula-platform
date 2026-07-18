import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { getCurrentUser, logout as authLogout, refreshToken } from '../services/auth';
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
      const stored = localStorage.getItem('gula_citizen_user');
      if (stored) {
        setUser(JSON.parse(stored));
      }

      if (localStorage.getItem('gula_citizen_token')) {
        await refreshToken();
        const currentUser = await getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
        }
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  const login = useCallback((userData: CitizenUser) => {
    setUser(userData);
    localStorage.setItem('gula_citizen_user', JSON.stringify(userData));
  }, []);

  const logout = useCallback(() => {
    authLogout();
    setUser(null);
  }, []);

  const updateUser = useCallback((updates: Partial<CitizenUser>) => {
    setUser((prev) => {
      if (!prev) return prev;
      const updated = { ...prev, ...updates };
      localStorage.setItem('gula_citizen_user', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const refreshAuth = useCallback(async () => {
    await refreshToken();
    const currentUser = await getCurrentUser();
    if (currentUser) setUser(currentUser);
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
