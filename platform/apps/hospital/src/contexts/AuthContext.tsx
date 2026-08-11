import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { apiRequest, setAuthToken } from '../services/api';

export interface HospitalUser {
  id: string;
  name: string;
  nameAr: string;
  email: string;
  title: string;
  titleAr: string;
  department: string;
  departmentAr: string;
  hospitalId: string;
  role: 'admin' | 'director' | 'manager' | 'doctor' | 'nurse' | 'finance' | 'hr' | 'bio_medical';
  permissions: string[];
  avatar?: string;
}

interface AuthContextValue {
  user: HospitalUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string, refreshToken: string, user: HospitalUser) => void;
  logout: () => void;
  updateUser: (updates: Partial<HospitalUser>) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<HospitalUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initAuth();
  }, []);

  async function initAuth() {
    try {
      const response = await apiRequest<{ user: HospitalUser }>('/auth/session');
      setUser(response.user);
    } catch {
      // offline
    } finally {
      setIsLoading(false);
    }
  }

  const login = useCallback((_token: string, _refreshToken: string, userData: HospitalUser) => {
    // Backend login establishes the HttpOnly cookies; retain only display state.
    setAuthToken(null, null);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    void apiRequest('/auth/logout', { method: 'POST', skipAuth: true }).catch(() => undefined);
    setAuthToken(null, null);
    setUser(null);
  }, []);

  const updateUser = useCallback((updates: Partial<HospitalUser>) => {
    setUser(prev => {
      if (!prev) return null;
      return { ...prev, ...updates };
    });
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
