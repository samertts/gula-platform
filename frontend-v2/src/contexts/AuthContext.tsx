import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, clearTokens } from '../api';
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

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = useCallback(async (email: string, password: string) => {
    // The backend sets Secure/HttpOnly access and refresh cookies.
    const response = await authApi.login(email, password);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Clear client state even when the server session is already expired.
    }
    clearTokens();
    setUser(null);
    localStorage.removeItem('gula_demo_user');
  }, []);

  useEffect(() => {
    let active = true;
    const verifySession = async () => {
      try {
        const session = await authApi.getSession();
        if (active) setUser(session.user);
      } catch {
        if (active) {
          clearTokens();
          setUser(null);
        }
      } finally {
        if (active) setIsLoading(false);
      }
    };
    void verifySession();
    return () => {
      active = false;
    };
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
