import { openDB, type IDBPDatabase } from 'idb';
import { processOfflineQueue } from './api';

interface SyncStatus {
  lastSync: string | null;
  pendingItems: number;
  isSyncing: boolean;
  lastSyncResult?: 'success' | 'failed' | 'partial';
  errors?: string[];
}

interface OfflineCacheEntry {
  key: string;
  data: unknown;
  timestamp: number;
  priority: 'critical' | 'high' | 'normal' | 'low';
  ttl: number;
}

let db: IDBPDatabase | null = null;
let syncInProgress = false;
let statusListeners: Array<(status: SyncStatus) => void> = [];
let onlineListeners: Array<() => void> = [];
let offlineListeners: Array<() => void> = [];
let currentStatus: SyncStatus = {
  lastSync: localStorage.getItem('gula_doctor_last_sync'),
  pendingItems: 0,
  isSyncing: false,
};

async function getDB(): Promise<IDBPDatabase> {
  if (db) return db;
  db = await openDB('gula-doctor-offline-sync', 1, {
    upgrade(database) {
      if (!database.objectStoreNames.contains('cache')) {
        database.createObjectStore('cache', { keyPath: 'key' });
      }
      if (!database.objectStoreNames.contains('pending')) {
        database.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
      }
    },
  });
  return db;
}

function notifyStatus() {
  statusListeners.forEach(listener => listener({ ...currentStatus }));
}

export function onOnline(callback: () => void) {
  onlineListeners.push(callback);
  return () => {
    onlineListeners = onlineListeners.filter(l => l !== callback);
  };
}

export function onOffline(callback: () => void) {
  offlineListeners.push(callback);
  return () => {
    offlineListeners = offlineListeners.filter(l => l !== callback);
  };
}

export function subscribeToStatus(callback: (status: SyncStatus) => void) {
  statusListeners.push(callback);
  callback({ ...currentStatus });
  return () => {
    statusListeners = statusListeners.filter(l => l !== callback);
  };
}

export async function getSyncStatus(): Promise<SyncStatus> {
  try {
    const database = await getDB();
    const pendingCount = await database.count('pending');
    currentStatus.pendingItems = pendingCount;
  } catch {
    currentStatus.pendingItems = 0;
  }
  return { ...currentStatus };
}

export async function getQueueLength(): Promise<number> {
  try {
    const database = await getDB();
    return await database.count('pending');
  } catch {
    return 0;
  }
}

export async function syncNow(): Promise<SyncStatus> {
  if (syncInProgress) return currentStatus;
  syncInProgress = true;
  currentStatus.isSyncing = true;
  notifyStatus();

  try {
    await processOfflineQueue();
    currentStatus.lastSync = new Date().toISOString();
    localStorage.setItem('gula_doctor_last_sync', currentStatus.lastSync);
    currentStatus.pendingItems = 0;
    currentStatus.lastSyncResult = 'success';
    currentStatus.errors = [];
  } catch (error) {
    currentStatus.lastSyncResult = 'failed';
    currentStatus.errors = [error instanceof Error ? error.message : 'Sync failed'];
  } finally {
    currentStatus.isSyncing = false;
    syncInProgress = false;
    notifyStatus();
  }

  return { ...currentStatus };
}

export function startBackgroundSync() {
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
}

export function stopBackgroundSync() {
  window.removeEventListener('online', handleOnline);
  window.removeEventListener('offline', handleOffline);
}

function handleOnline() {
  syncNow();
  onlineListeners.forEach(l => l());
}

function handleOffline() {
  offlineListeners.forEach(l => l());
}

export async function cacheData(
  key: string,
  data: unknown,
  priority: 'critical' | 'high' | 'normal' | 'low' = 'normal',
  ttlMinutes = 60,
) {
  try {
    const database = await getDB();
    await database.put('cache', {
      key,
      data,
      timestamp: Date.now(),
      priority,
      ttl: ttlMinutes * 60 * 1000,
    } as OfflineCacheEntry);
  } catch {}
}

export async function getCachedData<T>(key: string): Promise<T | null> {
  try {
    const database = await getDB();
    const entry: OfflineCacheEntry | undefined = await database.get('cache', key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > entry.ttl) {
      await database.delete('cache', key);
      return null;
    }
    return entry.data as T;
  } catch {
    return null;
  }
}

export async function clearAllCache() {
  try {
    const database = await getDB();
    await database.clear('cache');
  } catch {}
}

export async function queueForSync(data: Record<string, unknown>) {
  const database = await getDB();
  await database.add('pending', {
    ...data,
    timestamp: Date.now(),
    retryCount: 0,
  });
  currentStatus.pendingItems++;
  notifyStatus();

  if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await (registration as any).sync.register('sync-offline-queue');
    } catch {}
  }
}

export async function getPendingItems(): Promise<Record<string, unknown>[]> {
  const database = await getDB();
  return database.getAll('pending');
}
