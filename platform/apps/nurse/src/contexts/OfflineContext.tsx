import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { offlineService } from '@/services/offline';

interface OfflineContextValue {
  isOnline: boolean;
  pendingCount: number;
  lastSync: Date | null;
  enqueue: (item: Parameters<typeof offlineService.enqueue>[0]) => ReturnType<typeof offlineService.enqueue>;
  syncAll: () => Promise<void>;
}

const OfflineContext = createContext<OfflineContextValue | null>(null);

export function OfflineProvider({ children }: { children: ReactNode }) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  const updatePendingCount = useCallback(async () => {
    const count = await offlineService.getPendingCount();
    setPendingCount(count);
  }, []);

  useEffect(() => {
    const goOnline = () => { setIsOnline(true); };
    const goOffline = () => { setIsOnline(false); };
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    updatePendingCount();
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, [updatePendingCount]);

  const enqueue = useCallback(async (item: Parameters<typeof offlineService.enqueue>[0]) => {
    const entry = await offlineService.enqueue(item);
    await updatePendingCount();
    return entry;
  }, [updatePendingCount]);

  const syncAll = useCallback(async () => {
    await offlineService.syncAll(async (item) => {
      console.log('[Offline] Syncing item:', item.id);
    });
    await updatePendingCount();
    setLastSync(new Date());
  }, [updatePendingCount]);

  return (
    <OfflineContext.Provider value={{ isOnline, pendingCount, lastSync, enqueue, syncAll }}>
      {children}
    </OfflineContext.Provider>
  );
}

export function useOffline() {
  const ctx = useContext(OfflineContext);
  if (!ctx) throw new Error('useOffline must be used within OfflineProvider');
  return ctx;
}
