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
  /** Retained for API compatibility; browser persistence is intentionally disabled. */
  storageKey?: string;
  /** Retained for API compatibility; bearer tokens must not be persisted in web storage. */
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

function clearLegacyWebStorage(config: AuthConfig): void {
  try {
    localStorage.removeItem(config.storageKey ?? defaultConfig.storageKey!);
    localStorage.removeItem(config.tokenKey ?? defaultConfig.tokenKey!);
  } catch {
    // Storage may be unavailable in SSR/private browsing; memory state remains safe.
  }
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  status: 'loading',
  token: null,
  config: defaultConfig,

  setUser: (user: AuthUser, token: string) => {
    set({ user, status: 'authenticated', token });
    // The token remains memory-only. Production web authentication must use an
    // HttpOnly, Secure, SameSite cookie managed by the authoritative backend.
    clearLegacyWebStorage(get().config);
  },

  clearSession: () => {
    set({ user: null, status: 'unauthenticated', token: null });
    clearLegacyWebStorage(get().config);
  },

  updateUser: (updates: Partial<AuthUser>) => {
    const current = get().user;
    if (!current) return;
    set({ user: { ...current, ...updates } });
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
  // Deliberately do not restore bearer tokens from localStorage. The caller
  // should restore an HttpOnly-cookie session through the authoritative API.
  clearLegacyWebStorage(useAuth.getState().config);
  useAuth.getState().clearSession();
  return false;
};
