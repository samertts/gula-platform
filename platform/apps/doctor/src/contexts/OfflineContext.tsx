import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { subscribeToStatus, getQueueLength, syncNow, onOnline, onOffline } from '../services/offline';

interface SyncStatus {
  lastSync: string | null;
  pendingItems: number;
  isSyncing: boolean;
  lastSyncResult?: 'success' | 'failed' | 'partial';
  errors?: string[];
}

interface OfflineContextValue {
  isOnline: boolean;
  isOffline: boolean;
  syncStatus: SyncStatus;
  triggerSync: () => Promise<void>;
  queueLength: number;
}

const OfflineContext = createContext<OfflineContextValue | null>(null);

export function OfflineProvider({ children }: { children: ReactNode }) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    lastSync: localStorage.getItem('gula_doctor_last_sync'),
    pendingItems: 0,
    isSyncing: false,
  });
  const [queueLength, setQueueLength] = useState(0);

  useEffect(() => {
    const unsubStatus = subscribeToStatus((status) => {
      setSyncStatus(status);
    });

    const offOffline = onOffline(() => setIsOnline(false));
    const offOnline = onOnline(() => {
      setIsOnline(true);
      syncNow();
    });

    const interval = setInterval(async () => {
      const len = await getQueueLength();
      setQueueLength(len);
    }, 15000);

    return () => {
      unsubStatus();
      offOffline();
      offOnline();
      clearInterval(interval);
    };
  }, []);

  const triggerSync = useCallback(async () => {
    const status = await syncNow();
    setSyncStatus(status);
    setQueueLength(status.pendingItems);
  }, []);

  return (
    <OfflineContext.Provider
      value={{ isOnline, isOffline: !isOnline, syncStatus, triggerSync, queueLength }}
    >
      {children}
    </OfflineContext.Provider>
  );
}

export function useOfflineContext(): OfflineContextValue {
  const ctx = useContext(OfflineContext);
  if (!ctx) throw new Error('useOfflineContext must be used within OfflineProvider');
  return ctx;
}
