import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { Alert, MinistryUser, RegionData } from '../services/api';

interface MinistryContextValue {
  user: MinistryUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, otp: string) => Promise<void>;
  logout: () => void;
  regionFilter: string | null;
  setRegionFilter: (region: string | null) => void;
  dateRange: [Date, Date];
  setDateRange: (range: [Date, Date]) => void;
  alerts: Alert[];
}

const MinistryContext = createContext<MinistryContextValue | undefined>(undefined);

export function MinistryProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MinistryUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [regionFilter, setRegionFilter] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<[Date, Date]>([new Date(Date.now() - 30 * 86400000), new Date()]);
  const [alerts] = useState<Alert[]>([]);

  const login = useCallback(async (_email: string, _password: string, _otp: string) => {
    setIsLoading(true);
    try {
      await new Promise(r => setTimeout(r, 1000));
      setUser({
        id: 'min-001',
        name: 'مدير الوزارة',
        email: 'minister@health.gov.iq',
        role: 'minister',
        permissions: ['national_read', 'national_write', 'alerts_manage', 'reports_generate'],
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => setUser(null), []);

  return (
    <MinistryContext.Provider value={{
      user, isAuthenticated: !!user, isLoading,
      login, logout,
      regionFilter, setRegionFilter,
      dateRange, setDateRange,
      alerts,
    }}>
      {children}
    </MinistryContext.Provider>
  );
}

export function useMinistry() {
  const context = useContext(MinistryContext);
  if (!context) throw new Error('useMinistry must be used within MinistryProvider');
  return context;
}
