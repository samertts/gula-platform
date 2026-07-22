import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, setTokens, clearTokens, getAccessToken } from '../api';
import type { UserInfo } from '../api/types';

interface UserProfileLike {
  uid: string;
  id: string;
  name: string;
  email: string;
  role: string;
  labId?: string;
  wing?: string;
  verified?: boolean;
  createdAt?: string;
}

interface AuthContextType {
  user: UserInfo | null;
  profile: UserProfileLike | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  isLoading: true,
  login: async () => {},
  logout: async () => {},
  isAuthenticated: false,
});

export const useAuth = () => useContext(AuthContext);

const USER_KEY = 'gula_user_info';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(() => {
    const saved = localStorage.getItem(USER_KEY);
    return saved ? JSON.parse(saved) : null;
  });
  const [isLoading, setIsLoading] = useState(true);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setTokens(response.token, response.refresh_token);
    setUser(response.user);
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Proceed with local cleanup even if server logout fails
    }
    clearTokens();
    setUser(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem('gula_demo_user');
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    // Verify token is still valid on mount by fetching current user
    const verify = async () => {
      try {
    // Try a lightweight check - if 401 occurs, try refresh
        const storedUser = localStorage.getItem(USER_KEY);
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }
      } catch {
        // Token invalid, clear state
        clearTokens();
        setUser(null);
        localStorage.removeItem(USER_KEY);
      } finally {
        setIsLoading(false);
      }
    };
    verify();
  }, []);

  const profile = user ? {
    uid: user.id,
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    labId: user.lab_id || undefined,
  } : null;

  return (
    <AuthContext.Provider value={{ user, profile, isLoading, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};
