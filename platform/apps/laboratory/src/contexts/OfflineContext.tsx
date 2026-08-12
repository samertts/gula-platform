import { createContext, useContext, useState, useCallback, useEffect, useMemo, type ReactNode } from 'react';
import { openDB, type IDBPDatabase } from 'idb';
import {
  buildQueueRequestInit,
  classifyQueueResponse,
  createQueueEnvelope,
  inspectQueueRecord,
  nextQueueEnvelopeState,
  type OfflineQueueEnvelope,
} from '@gula/ui-platform';

interface OfflineQueueItem extends Partial<OfflineQueueEnvelope> {
  id?: number;
  url: string;
  method: string;
  body?: string;
  timestamp?: number;
  retryCount?: number;
  maxRetries?: number;
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
    dbPromise = openDB('gula-lab-offline', 2, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('requests')) {
          db.createObjectStore('requests', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' });
        }
        if (!db.objectStoreNames.contains('queue_rejections')) {
          db.createObjectStore('queue_rejections', { keyPath: 'id', autoIncrement: true });
        }
      },
    }).then(async (database) => {
      const requests = await database.getAll('requests');
      const tx = database.transaction(['requests', 'queue_rejections'], 'readwrite');
      for (const request of requests) {
        const result = inspectQueueRecord(request);
        if (!result.safe) {
          await tx.objectStore('queue_rejections').add({
            source: 'gula-lab-offline.requests',
            requestId: request.id,
            reason: result.reason,
            rejectedAt: Date.now(),
          });
          await tx.objectStore('requests').delete(request.id);
        }
      }
      await tx.done;
      return database;
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
      const envelope = await createQueueEnvelope({
        url,
        method,
        body,
        entityType: url.split('/').filter(Boolean).slice(-1)[0] || 'laboratory',
        action: method.toLowerCase(),
      });
      await db.add('requests', { ...envelope, timestamp: Date.now(), retryCount: 0, maxRetries: envelope.maxAttempts });
      await updatePendingCount();
    } catch (error) {
      setState(s => ({ ...s, syncError: error instanceof Error ? error.message : 'تعذر تخزين الطلب' }));
      throw error;
    }
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
          const result = inspectQueueRecord(req);
          if (!result.safe) {
            await db.add('queue_rejections', {
              source: 'gula-lab-offline.requests',
              requestId: req.id,
              url: req.url,
              method: req.method,
              reason: result.reason,
              rejectedAt: Date.now(),
            });
            await db.delete('requests', req.id);
            continue;
          }
          const envelope = req.schemaVersion === 1
            ? req as OfflineQueueEnvelope
            : await createQueueEnvelope({
              url: req.url,
              method: req.method,
              body: req.body,
              entityType: 'laboratory',
              action: req.method.toLowerCase(),
            });
          const response = await fetch(envelope.url, buildQueueRequestInit(envelope));
          const disposition = classifyQueueResponse(response.status);

          if (disposition === 'synced') {
            await db.delete('requests', req.id);
          } else if (disposition === 'conflict') {
            let serverBody: unknown;
            try { serverBody = await response.json(); } catch { /* no JSON body */ }
            await db.put('requests', {
              ...nextQueueEnvelopeState(envelope, disposition, `HTTP ${response.status}`, {
                status: response.status as 409 | 412,
                serverBody,
                detectedAt: new Date().toISOString(),
              }),
              id: req.id,
            });
          } else {
            await db.put('requests', {
              ...nextQueueEnvelopeState(envelope, disposition, `HTTP ${response.status}`),
              id: req.id,
            });
          }
        } catch (e) {
          const envelope = req.schemaVersion === 1 ? req as OfflineQueueEnvelope : await createQueueEnvelope({
            url: req.url,
            method: req.method,
            body: req.body,
            entityType: 'laboratory',
            action: req.method.toLowerCase(),
          });
          await db.put('requests', {
            ...nextQueueEnvelopeState(envelope, 'retry', (e as Error).message),
            id: req.id,
          });
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
