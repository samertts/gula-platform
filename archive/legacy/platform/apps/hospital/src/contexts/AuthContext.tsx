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
      const token = localStorage.getItem('gula_hospital_token');
      const stored = localStorage.getItem('gula_hospital_user');

      if (stored) {
        setUser(JSON.parse(stored));
      }

      if (token) {
        try {
          const currentUser = await apiRequest<HospitalUser>('/auth/me');
          setUser(currentUser);
          localStorage.setItem('gula_hospital_user', JSON.stringify(currentUser));
        } catch {
          localStorage.removeItem('gula_hospital_token');
          localStorage.removeItem('gula_hospital_refresh');
          localStorage.removeItem('gula_hospital_user');
        }
      }
    } catch {
      // offline
    } finally {
      setIsLoading(false);
    }
  }

  const login = useCallback((token: string, refreshToken: string, userData: HospitalUser) => {
    setAuthToken(token, refreshToken);
    setUser(userData);
    localStorage.setItem('gula_hospital_user', JSON.stringify(userData));
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null, null);
    setUser(null);
    localStorage.removeItem('gula_hospital_user');
  }, []);

  const updateUser = useCallback((updates: Partial<HospitalUser>) => {
    setUser(prev => {
      if (!prev) return null;
      const updated = { ...prev, ...updates };
      localStorage.setItem('gula_hospital_user', JSON.stringify(updated));
      return updated;
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
