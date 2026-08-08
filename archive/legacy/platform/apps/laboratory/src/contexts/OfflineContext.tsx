import { createContext, useContext, useState, useCallback, useEffect, useMemo, type ReactNode } from 'react';
import { openDB, type IDBPDatabase } from 'idb';

interface OfflineQueueItem {
  id?: number;
  url: string;
  method: string;
  body?: string;
  timestamp: number;
  retryCount: number;
  maxRetries: number;
  error?: string;
}

interface OfflineState {
  isOnline: boolean;
  isSyncing: boolean;
  pendingCount: number;
  lastSync: Date | null;
  queue: OfflineQueueItem[];
  syncError: string | null;
}

interface OfflineContextValue extends OfflineState {
  queueRequest: (url: string, method: string, body?: unknown) => Promise<void>;
  processQueue: () => Promise<void>;
  clearQueue: () => Promise<void>;
}

const OfflineContext = createContext<OfflineContextValue | null>(null);

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB('gula-lab-offline', 1, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('requests')) {
          db.createObjectStore('requests', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' });
        }
      },
    });
  }
  return dbPromise;
}

export function OfflineProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<OfflineState>({
    isOnline: navigator.onLine,
    isSyncing: false,
    pendingCount: 0,
    lastSync: null,
    queue: [],
    syncError: null,
  });

  const updatePendingCount = useCallback(async () => {
    try {
      const db = await getDb();
      const all = await db.getAll('requests');
      setState(s => ({ ...s, pendingCount: all.length, queue: all }));
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    const handleOnline = () => setState(s => ({ ...s, isOnline: true }));
    const handleOffline = () => setState(s => ({ ...s, isOnline: false }));

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    updatePendingCount();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [updatePendingCount]);

  const queueRequest = useCallback(async (url: string, method: string, body?: unknown) => {
    try {
      const db = await getDb();
      await db.add('requests', {
        url,
        method,
        body: body ? JSON.stringify(body) : undefined,
        timestamp: Date.now(),
        retryCount: 0,
        maxRetries: 5,
      });
      await updatePendingCount();
    } catch { /* ignore */ }
  }, [updatePendingCount]);

  const processQueue = useCallback(async () => {
    setState(s => ({ ...s, isSyncing: true, syncError: null }));
    try {
      const db = await getDb();
      const requests = await db.getAll('requests');

      for (const req of requests) {
        if (req.retryCount >= req.maxRetries) {
          await db.delete('requests', req.id);
          continue;
        }

        try {
          const response = await fetch(req.url, {
            method: req.method,
            headers: { 'Content-Type': 'application/json' },
            body: req.body,
          });

          if (response.ok) {
            await db.delete('requests', req.id);
          } else {
            await db.put('requests', { ...req, retryCount: req.retryCount + 1, error: `${response.status}` });
          }
        } catch (e) {
          await db.put('requests', { ...req, retryCount: req.retryCount + 1, error: (e as Error).message });
        }
      }

      await updatePendingCount();
      setState(s => ({ ...s, isSyncing: false, lastSync: new Date() }));
    } catch (e) {
      setState(s => ({ ...s, isSyncing: false, syncError: (e as Error).message }));
    }
  }, [updatePendingCount]);

  const clearQueue = useCallback(async () => {
    try {
      const db = await getDb();
      const all = await db.getAll('requests');
      for (const req of all) {
        if (req.id) await db.delete('requests', req.id);
      }
      await updatePendingCount();
    } catch { /* ignore */ }
  }, [updatePendingCount]);

  const value = useMemo(() => ({
    ...state,
    queueRequest,
    processQueue,
    clearQueue,
  }), [state, queueRequest, processQueue, clearQueue]);

  return <OfflineContext.Provider value={value}>{children}</OfflineContext.Provider>;
}

export function useOffline() {
  const ctx = useContext(OfflineContext);
  if (!ctx) throw new Error('useOffline must be used within OfflineProvider');
  return ctx;
}
