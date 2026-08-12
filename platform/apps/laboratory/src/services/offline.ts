import { openDB, type IDBPDatabase } from 'idb';
import { processOfflineQueue } from './api';
import { inspectQueuePayload } from '@gula/ui-platform';

interface SyncStatus {
  lastSync: Date | null;
  pendingItems: number;
  isSyncing: boolean;
  error?: string;
  syncedItems: number;
  failedItems: number;
}

type StorageListener = (key: string, value: unknown) => void;

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB('gula-lab-offline-store', 3, {
      upgrade(db, oldVersion, _newVersion, transaction) {
        if (oldVersion < 1) {
          db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
          db.createObjectStore('cache', { keyPath: 'key' });
          db.createObjectStore('drafts', { keyPath: 'id' });
          db.createObjectStore('sync_log', { keyPath: 'id', autoIncrement: true });
        }
        if (oldVersion < 2 && db.objectStoreNames.contains('pending') && transaction) {
          const pending = transaction.objectStore('pending');
          if (!pending.indexNames.contains('entity_type')) {
            pending.createIndex('entity_type', 'entityType');
          }
        }
        if (!db.objectStoreNames.contains('queue_rejections')) {
          db.createObjectStore('queue_rejections', { keyPath: 'id', autoIncrement: true });
        }
      },
    }).then(async (database) => {
      const pending = await database.getAll('pending');
      const tx = database.transaction(['pending', 'queue_rejections', 'sync_log'], 'readwrite');
      for (const item of pending) {
        const result = inspectQueuePayload(item);
        if (!result.safe) {
          await tx.objectStore('queue_rejections').add({
            source: 'gula-lab-offline-store.pending',
            requestId: item.id,
            reason: result.reason,
            rejectedAt: Date.now(),
          });
          await tx.objectStore('sync_log').add({
            entityId: item.entityId,
            entityType: item.entityType,
            action: item.action,
            status: 'rejected',
            error: result.reason,
            timestamp: new Date().toISOString(),
          });
          await tx.objectStore('pending').delete(item.id);
        }
      }
      await tx.done;
      return database;
    });
  }
  return dbPromise;
}

export const offlineService = {
  async saveDraft(key: string, data: unknown): Promise<void> {
    const db = await getDb();
    await db.put('drafts', { id: key, data, updatedAt: new Date().toISOString() });
  },

  async getDraft<T = unknown>(key: string): Promise<T | null> {
    const db = await getDb();
    const entry = await db.get('drafts', key);
    return entry?.data ?? null;
  },

  async deleteDraft(key: string): Promise<void> {
    const db = await getDb();
    await db.delete('drafts', key);
  },

  async listDrafts(): Promise<{ id: string; updatedAt: string }[]> {
    const db = await getDb();
    return db.getAll('drafts');
  },

  async cacheData(key: string, data: unknown, ttlMs = 30 * 60 * 1000): Promise<void> {
    const db = await getDb();
    await db.put('cache', { key, data, expiresAt: Date.now() + ttlMs });
  },

  async getCachedData<T = unknown>(key: string): Promise<T | null> {
    const db = await getDb();
    const entry = await db.get('cache', key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      await db.delete('cache', key);
      return null;
    }
    return entry.data as T;
  },

  async invalidateCache(key: string): Promise<void> {
    const db = await getDb();
    await db.delete('cache', key);
  },

  async clearAllCache(): Promise<void> {
    const db = await getDb();
    const all = await db.getAll('cache');
    for (const entry of all) {
      await db.delete('cache', entry.key);
    }
  },

  async getSyncStatus(): Promise<SyncStatus> {
    const db = await getDb();
    const pending = await db.getAll('pending');
    const logs = await db.getAll('sync_log');
    const lastLog = logs[logs.length - 1];

    return {
      lastSync: lastLog?.timestamp ? new Date(lastLog.timestamp) : null,
      pendingItems: pending.length,
      isSyncing: false,
      syncedItems: logs.filter((l: any) => l.status === 'synced').length,
      failedItems: logs.filter((l: any) => l.status === 'failed').length,
    };
  },

  async syncAll(): Promise<SyncStatus> {
    const db = await getDb();
    const pending = await db.getAll('pending');
    let synced = 0;
    let failed = 0;

    for (const item of pending) {
      try {
        const result = inspectQueuePayload(item);
        if (!result.safe) {
          await db.delete('pending', item.id);
          await db.add('queue_rejections', {
            source: 'gula-lab-offline-store.pending',
            requestId: item.id,
            reason: result.reason,
            rejectedAt: Date.now(),
          });
          await db.add('sync_log', {
            entityId: item.entityId,
            entityType: item.entityType,
            action: item.action,
            status: 'rejected',
            error: result.reason,
            timestamp: new Date().toISOString(),
          });
          failed++;
          continue;
        }
        const response = await fetch(item.url, {
          method: item.method || 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: item.body ? JSON.stringify(item.body) : undefined,
        });
        if (response.ok) {
          await db.delete('pending', item.id);
          await db.add('sync_log', {
            entityId: item.entityId,
            entityType: item.entityType,
            action: item.action,
            status: 'synced',
            timestamp: new Date().toISOString(),
          });
          synced++;
        } else {
          failed++;
          await db.add('sync_log', {
            entityId: item.entityId,
            entityType: item.entityType,
            action: item.action,
            status: 'failed',
            error: `${response.status} ${response.statusText}`,
            timestamp: new Date().toISOString(),
          });
        }
      } catch (e) {
        failed++;
        await db.add('sync_log', {
          entityId: item.entityId,
          entityType: item.entityType,
          action: item.action,
          status: 'failed',
          error: (e as Error).message,
          timestamp: new Date().toISOString(),
        });
      }
    }

    try {
      await processOfflineQueue();
    } catch { /* ignore */ }

    const remaining = await db.getAll('pending');
    return {
      lastSync: new Date(),
      pendingItems: remaining.length,
      isSyncing: false,
      syncedItems: synced,
      failedItems: failed,
    };
  },

  async addToPending(data: {
    url: string;
    method?: string;
    body?: unknown;
    entityType: string;
    entityId?: string;
    action: string;
  }): Promise<void> {
    const db = await getDb();
    const result = inspectQueuePayload(data);
    if (!result.safe) {
      await db.add('queue_rejections', {
        source: 'gula-lab-offline-store.pending',
        entityType: data.entityType,
        entityId: data.entityId,
        reason: result.reason,
        rejectedAt: Date.now(),
      });
      throw new Error('تم رفض تخزين عنصر غير متصل يحتوي بيانات اعتماد');
    }
    await db.add('pending', {
      ...data,
      timestamp: new Date().toISOString(),
      retryCount: 0,
      maxRetries: 5,
    });
  },

  async getPendingCount(): Promise<number> {
    const db = await getDb();
    const all = await db.getAll('pending');
    return all.length;
  },

  async clearPending(): Promise<void> {
    const db = await getDb();
    const all = await db.getAll('pending');
    for (const item of all) {
      if (item.id) await db.delete('pending', item.id);
    }
  },

  async subscribeToStorageChanges(listener: StorageListener): Promise<() => void> {
    const handleStorage = (e: StorageEvent) => {
      if (e.newValue !== null) {
        try { listener(e.key!, JSON.parse(e.newValue)); }
        catch { listener(e.key!, e.newValue); }
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  },
};
