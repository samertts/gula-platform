import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from 'react';
import type { LabUser, LabRole, Sample, Analyzer, AuditEntry } from '@/utils/types';

interface LabState {
  user: LabUser | null;
  labId: string | null;
  labName: string;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface LabContextValue extends LabState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: LabUser) => void;
  setLabInfo: (id: string, name: string) => void;
  hasRole: (...roles: LabRole[]) => boolean;
}

const LabContext = createContext<LabContextValue | null>(null);

export function LabProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LabState>({
    user: null,
    labId: null,
    labName: '',
    isAuthenticated: false,
    isLoading: false,
  });

  const login = useCallback(async (email: string, _password: string) => {
    setState(s => ({ ...s, isLoading: true }));
    try {
      const response = await fetch(`/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: _password }),
      });
      if (!response.ok) throw new Error('Login failed');
      const data = await response.json();
      setState({
        user: data.user,
        labId: data.labId,
        labName: data.labName,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      setState(s => ({ ...s, isLoading: false }));
      throw new Error('فشل تسجيل الدخول');
    }
  }, []);

  const logout = useCallback(() => {
    setState({
      user: null,
      labId: null,
      labName: '',
      isAuthenticated: false,
      isLoading: false,
    });
  }, []);

  const setUser = useCallback((user: LabUser) => {
    setState(s => ({ ...s, user }));
  }, []);

  const setLabInfo = useCallback((id: string, name: string) => {
    setState(s => ({ ...s, labId: id, labName: name }));
  }, []);

  const hasRole = useCallback((...roles: LabRole[]) => {
    if (!state.user) return false;
    return roles.includes(state.user.role);
  }, [state.user]);

  const value = useMemo(() => ({
    ...state,
    login,
    logout,
    setUser,
    setLabInfo,
    hasRole,
  }), [state, login, logout, setUser, setLabInfo, hasRole]);

  return <LabContext.Provider value={value}>{children}</LabContext.Provider>;
}

export function useLab() {
  const ctx = useContext(LabContext);
  if (!ctx) throw new Error('useLab must be used within LabProvider');
  return ctx;
}
