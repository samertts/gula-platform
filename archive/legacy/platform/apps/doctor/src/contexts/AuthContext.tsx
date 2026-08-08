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
      const token = localStorage.getItem('gula_doctor_token');
      const stored = localStorage.getItem('gula_doctor_user');

      if (stored) {
        setUser(JSON.parse(stored));
      }

      if (token) {
        try {
          const currentUser = await apiRequest<DoctorUser>('/auth/me');
          setUser(currentUser);
          localStorage.setItem('gula_doctor_user', JSON.stringify(currentUser));
        } catch {
          localStorage.removeItem('gula_doctor_token');
          localStorage.removeItem('gula_doctor_refresh');
          localStorage.removeItem('gula_doctor_user');
          setUser(null);
        }
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  const login = useCallback((token: string, refresh: string, userData: DoctorUser) => {
    setAuthToken(token, refresh);
    setUser(userData);
    localStorage.setItem('gula_doctor_user', JSON.stringify(userData));
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null, null);
    setUser(null);
    localStorage.removeItem('gula_doctor_user');
  }, []);

  const updateUser = useCallback((updates: Partial<DoctorUser>) => {
    setUser((prev) => {
      if (!prev) return prev;
      const updated = { ...prev, ...updates };
      localStorage.setItem('gula_doctor_user', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const refreshAuth = useCallback(async () => {
    const token = localStorage.getItem('gula_doctor_token');
    if (!token) return;
    try {
      const currentUser = await apiRequest<DoctorUser>('/auth/me');
      setUser(currentUser);
      localStorage.setItem('gula_doctor_user', JSON.stringify(currentUser));
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
