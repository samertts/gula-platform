import { create } from 'zustand';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: string;
  labId?: string;
  permissions: string[];
  metadata?: Record<string, unknown>;
}

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

export interface AuthConfig {
  storageKey?: string;
  tokenKey?: string;
  refreshThreshold?: number;
}

interface AuthState {
  user: AuthUser | null;
  status: AuthStatus;
  token: string | null;
  config: AuthConfig;
  setUser: (user: AuthUser, token: string) => void;
  clearSession: () => void;
  updateUser: (updates: Partial<AuthUser>) => void;
  hasPermission: (permission: string, resource?: string) => boolean;
  hasRole: (role: string) => boolean;
  isAuthenticated: () => boolean;
}

const defaultConfig: AuthConfig = {
  storageKey: 'gula-auth',
  tokenKey: 'gula-token',
  refreshThreshold: 300,
};

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  status: 'loading',
  token: null,
  config: defaultConfig,

  setUser: (user: AuthUser, token: string) => {
    set({ user, status: 'authenticated', token });
    try {
      localStorage.setItem(get().config.storageKey!, JSON.stringify(user));
      localStorage.setItem(get().config.tokenKey!, token);
    } catch {}
  },

  clearSession: () => {
    set({ user: null, status: 'unauthenticated', token: null });
    try {
      localStorage.removeItem(get().config.storageKey!);
      localStorage.removeItem(get().config.tokenKey!);
    } catch {}
  },

  updateUser: (updates: Partial<AuthUser>) => {
    const current = get().user;
    if (!current) return;
    const updated = { ...current, ...updates };
    set({ user: updated });
    try {
      localStorage.setItem(get().config.storageKey!, JSON.stringify(updated));
    } catch {}
  },

  hasPermission: (permission: string, resource?: string): boolean => {
    const user = get().user;
    if (!user) return false;
    if (user.role === 'admin' || user.role === 'master_admin') return true;
    if (resource) {
      return user.permissions.some((p) => p === `${resource}:${permission}` || p === `${resource}:*` || p === '*:*');
    }
    return user.permissions.some((p) => p === permission || p === '*:*');
  },

  hasRole: (role: string): boolean => {
    const user = get().user;
    if (!user) return false;
    if (user.role === 'master_admin') return true;
    return user.role === role;
  },

  isAuthenticated: () => get().status === 'authenticated' && !!get().user,
}));

export const restoreSession = (): boolean => {
  try {
    const stored = localStorage.getItem('gula-auth');
    const token = localStorage.getItem('gula-token');
    if (stored && token) {
      const user = JSON.parse(stored) as AuthUser;
      useAuth.getState().setUser(user, token);
      return true;
    }
  } catch {}
  useAuth.getState().clearSession();
  return false;
};
