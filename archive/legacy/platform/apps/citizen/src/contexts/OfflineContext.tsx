import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { getSyncStatus, getQueueLength, onOnline, onOffline } from '../services/offline';
import { startBackgroundSync, stopBackgroundSync, syncNow } from '../services/sync';
import type { SyncStatus } from '../types';

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
    lastSync: null,
    pendingItems: 0,
    isSyncing: false,
  });
  const [queueLength, setQueueLength] = useState(0);

  useEffect(() => {
    const off = onOffline(() => setIsOnline(false));
    const on = onOnline(() => {
      setIsOnline(true);
      syncNow();
    });

    startBackgroundSync();
    updateStatus();

    const interval = setInterval(updateStatus, 30000);
    return () => {
      off();
      on();
      stopBackgroundSync();
      clearInterval(interval);
    };
  }, []);

  async function updateStatus() {
    const status = await getSyncStatus();
    setSyncStatus(status);
    const len = await getQueueLength();
    setQueueLength(len);
  }

  const triggerSync = useCallback(async () => {
    await syncNow();
    await updateStatus();
  }, []);

  return (
    <OfflineContext.Provider
      value={{ isOnline, isOffline: !isOnline, syncStatus, triggerSync, queueLength }}
    >
      {children}
    </OfflineContext.Provider>
  );
}

export function useOffline(): OfflineContextValue {
  const ctx = useContext(OfflineContext);
  if (!ctx) throw new Error('useOffline must be used within OfflineProvider');
  return ctx;
}
