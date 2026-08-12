import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { apiRequest, setAuthToken } from '../services/api';

export interface DoctorUser {
  id: string;
  name: string;
  nameAr: string;
  email: string;
  title: string;
  titleAr: string;
  specialization: string;
  specializationAr: string;
  licenseNumber: string;
  labId: string;
  facilityId: string;
  department: string;
  role: 'doctor' | 'consultant' | 'specialist' | 'resident' | 'nurse' | 'admin';
  permissions: string[];
  mfaEnabled: boolean;
  avatar?: string;
}

interface AuthContextValue {
  user: DoctorUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string, refreshToken: string, user: DoctorUser) => void;
  logout: () => void;
  updateUser: (updates: Partial<DoctorUser>) => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DoctorUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initAuth();
  }, []);

  async function initAuth() {
    try {
      const response = await apiRequest<{ user: DoctorUser }>('/auth/session');
      setUser(response.user);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  const login = useCallback((_token: string, _refresh: string, userData: DoctorUser) => {
    // Backend login establishes the HttpOnly cookies; retain only display state.
    setAuthToken(null, null);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    void apiRequest('/auth/logout', { method: 'POST', skipAuth: true }).catch(() => undefined);
    setAuthToken(null, null);
    setUser(null);
  }, []);

  const updateUser = useCallback((updates: Partial<DoctorUser>) => {
    setUser((prev) => {
      if (!prev) return prev;
      return { ...prev, ...updates };
    });
  }, []);

  const refreshAuth = useCallback(async () => {
    try {
      const response = await apiRequest<{ user: DoctorUser }>('/auth/session');
      setUser(response.user);
    } catch {
      logout();
    }
  }, [logout]);

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
