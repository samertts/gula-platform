import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { loginUser, logoutUser } from '@/services/api';
import type { User } from '@/utils/types';

interface NurseContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  selectedWard: string;
  setSelectedWard: (ward: string) => void;
}

const NurseContext = createContext<NurseContextValue | null>(null);

export function NurseProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedWard, setSelectedWard] = useState('');

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await loginUser(email, password);
      setUser(data.user as User);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
  }, []);

  return (
    <NurseContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        selectedWard,
        setSelectedWard,
      }}
    >
      {children}
    </NurseContext.Provider>
  );
}

export function useNurse() {
  const ctx = useContext(NurseContext);
  if (!ctx) throw new Error('useNurse must be used within NurseProvider');
  return ctx;
}
