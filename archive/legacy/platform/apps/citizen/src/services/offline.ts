import { openDB, type IDBPDatabase } from 'idb';
import type { OfflineQueueItem, SyncStatus, CitizenUser, FamilyMember, LabResult, Appointment, Notification, EmergencyInfo } from '../types';

const DB_NAME = 'gula-citizen-offline';
const DB_VERSION = 2;

let dbInstance: IDBPDatabase | null = null;

async function getDB(): Promise<IDBPDatabase> {
  if (dbInstance) return dbInstance;

  dbInstance = await openDB(DB_NAME, DB_VERSION, {
    upgrade(db, oldVersion) {
      if (oldVersion < 1) {
        db.createObjectStore('requests', { keyPath: 'id', autoIncrement: true });
        db.createObjectStore('cache', { keyPath: 'key' });
        db.createObjectStore('health_data', { keyPath: 'id' });
        db.createObjectStore('family', { keyPath: 'id' });
        db.createObjectStore('appointments', { keyPath: 'id' });
        db.createObjectStore('notifications', { keyPath: 'id' });
      }
      if (oldVersion < 2) {
        if (!db.objectStoreNames.contains('emergency')) {
          db.createObjectStore('emergency', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('sync_meta')) {
          db.createObjectStore('sync_meta', { keyPath: 'key' });
        }
      }
    },
  });

  return dbInstance;
}

export async function cacheHealthData(data: LabResult[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('health_data', 'readwrite');
  for (const item of data) {
    await tx.store.put(item);
  }
  await tx.done;
}

export async function getCachedHealthData(): Promise<LabResult[]> {
  const db = await getDB();
  return db.getAll('health_data');
}

export async function cacheAppointments(data: Appointment[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('appointments', 'readwrite');
  for (const item of data) {
    await tx.store.put(item);
  }
  await tx.done;
}

export async function getCachedAppointments(): Promise<Appointment[]> {
  const db = await getDB();
  return db.getAll('appointments');
}

export async function cacheNotifications(data: Notification[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('notifications', 'readwrite');
  for (const item of data) {
    await tx.store.put(item);
  }
  await tx.done;
}

export async function getCachedNotifications(): Promise<Notification[]> {
  const db = await getDB();
  return db.getAll('notifications');
}

export async function cacheFamily(data: FamilyMember[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('family', 'readwrite');
  for (const item of data) {
    await tx.store.put(item);
  }
  await tx.done;
}

export async function getCachedFamily(): Promise<FamilyMember[]> {
  const db = await getDB();
  return db.getAll('family');
}

export async function saveEmergencyInfo(data: EmergencyInfo): Promise<void> {
  const db = await getDB();
  await db.put('emergency', { id: 'emergency_info', ...data });
}

export async function getEmergencyInfo(): Promise<EmergencyInfo | null> {
  const db = await getDB();
  const data = await db.get('emergency', 'emergency_info');
  if (!data) return null;
  const { id, ...info } = data as any;
  return info as EmergencyInfo;
}

export async function updateSyncTimestamp(): Promise<void> {
  const db = await getDB();
  await db.put('sync_meta', { key: 'last_sync', timestamp: Date.now() });
}

export async function getLastSyncTimestamp(): Promise<number | null> {
  const db = await getDB();
  const meta = await db.get('sync_meta', 'last_sync');
  return meta?.timestamp ?? null;
}

export async function getSyncStatus(): Promise<SyncStatus> {
  const db = await getDB();
  const pendingItems = await db.count('requests');
  const lastSync = await getLastSyncTimestamp();

  return {
    lastSync: lastSync ? new Date(lastSync) : null,
    pendingItems,
    isSyncing: false,
  };
}

export async function getQueueLength(): Promise<number> {
  const db = await getDB();
  return db.count('requests');
}

export async function clearAllCachedData(): Promise<void> {
  const db = await getDB();
  const stores = ['health_data', 'family', 'appointments', 'notifications', 'emergency', 'cache', 'requests'];
  const tx = db.transaction(stores, 'readwrite');
  for (const store of stores) {
    await tx.objectStore(store).clear();
  }
  await tx.done;
}

export async function getOfflineQueue(): Promise<OfflineQueueItem[]> {
  const db = await getDB();
  return db.getAll('requests');
}

export async function removeFromQueue(id: number): Promise<void> {
  const db = await getDB();
  await db.delete('requests', id);
}

export async function getCachedUser(): Promise<CitizenUser | null> {
  try {
    const raw = localStorage.getItem('gula_citizen_user');
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

export async function getCacheSize(): Promise<string> {
  const db = await getDB();
  let totalSize = 0;
  const stores = ['health_data', 'family', 'appointments', 'notifications', 'emergency', 'cache'];
  for (const storeName of stores) {
    const all = await db.getAll(storeName);
    for (const item of all) {
      totalSize += new Blob([JSON.stringify(item)]).size;
    }
  }
  if (totalSize < 1024) return `${totalSize} B`;
  if (totalSize < 1024 * 1024) return `${(totalSize / 1024).toFixed(1)} KB`;
  return `${(totalSize / (1024 * 1024)).toFixed(1)} MB`;
}

export function isOnline(): boolean {
  return navigator.onLine;
}

export function onOnline(callback: () => void): () => void {
  window.addEventListener('online', callback);
  return () => window.removeEventListener('online', callback);
}

export function onOffline(callback: () => void): () => void {
  window.addEventListener('offline', callback);
  return () => window.removeEventListener('offline', callback);
}
