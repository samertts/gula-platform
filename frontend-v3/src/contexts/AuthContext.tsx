import { createContext, useContext, useReducer, useEffect, useCallback, type ReactNode } from 'react';
import type { LabUser, Lab, UserRole } from '@/types/backend';
import { api, setTokens, clearTokens } from '@/api/client';
import { auth as authApi } from '@/api/endpoints';

interface AuthState {
  user: LabUser | null;
  lab: Lab | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; user: LabUser; lab: Lab }
  | { type: 'AUTH_FAILURE'; error: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_USER'; user: LabUser }
  | { type: 'SET_LAB'; lab: Lab };

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  can: (permission: string) => boolean;
  isPlatformRole: boolean;
}

const initialState: AuthState = {
  user: null,
  lab: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, isLoading: true, error: null };
    case 'AUTH_SUCCESS':
      return { user: action.user, lab: action.lab, isAuthenticated: true, isLoading: false, error: null };
    case 'AUTH_FAILURE':
      return { ...initialState, isLoading: false, error: action.error };
    case 'LOGOUT':
      return { ...initialState, isLoading: false };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    case 'SET_USER':
      return { ...state, user: action.user };
    case 'SET_LAB':
      return { ...state, lab: action.lab };
    default:
      return state;
  }
}

const AuthContext = createContext<AuthContextType | null>(null);

const PLATFORM_ROLES: UserRole[] = ['master_admin', 'ministry_admin', 'province_admin'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  const tryRestoreSession = useCallback(async () => {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      dispatch({ type: 'LOGOUT' });
      return;
    }
    try {
      const user = await api.get('/auth/check').then((r) => r.data);
      const lab = await api.get('/labs/me').then((r) => r.data);
      dispatch({ type: 'AUTH_SUCCESS', user, lab });
    } catch {
      clearTokens();
      dispatch({ type: 'LOGOUT' });
    }
  }, []);

  useEffect(() => {
    tryRestoreSession();
  }, [tryRestoreSession]);

  const login = useCallback(async (email: string, password: string) => {
    dispatch({ type: 'AUTH_START' });
    try {
      const response = await authApi.login({ username: email, password });
      setTokens(response.access_token, response.refresh_token);
      dispatch({ type: 'AUTH_SUCCESS', user: response.user, lab: response.lab });
    } catch (err: any) {
      dispatch({ type: 'AUTH_FAILURE', error: err.message || 'فشل تسجيل الدخول' });
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch { /* ignore */ }
    clearTokens();
    dispatch({ type: 'LOGOUT' });
  }, []);

  const can = useCallback(
    (permission: string) => {
      if (!state.user) return false;
      return PLATFORM_ROLES.includes(state.user.role) || true;
    },
    [state.user]
  );

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        clearError: () => dispatch({ type: 'CLEAR_ERROR' }),
        can,
        isPlatformRole: state.user ? PLATFORM_ROLES.includes(state.user.role) : false,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
