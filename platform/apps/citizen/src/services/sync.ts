import { processOfflineQueue } from './api';
import {
  updateSyncTimestamp,
  getLastSyncTimestamp,
  getQueueLength,
} from './offline';
import { SYNC_INTERVALS } from '../utils/constants';

type SyncListener = (status: 'syncing' | 'completed' | 'error', error?: string) => void;

const listeners: Set<SyncListener> = new Set();
let syncTimer: ReturnType<typeof setInterval> | null = null;
let isSyncing = false;

export function addSyncListener(listener: SyncListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notifyListeners(status: 'syncing' | 'completed' | 'error', error?: string) {
  listeners.forEach((l) => l(status, error));
}

export async function syncNow(): Promise<void> {
  if (isSyncing || !navigator.onLine) return;
  isSyncing = true;
  notifyListeners('syncing');

  try {
    await processOfflineQueue();
    await updateSyncTimestamp();
    isSyncing = false;
    notifyListeners('completed');
  } catch (error) {
    isSyncing = false;
    notifyListeners('error', (error as Error).message);
  }
}

export function startBackgroundSync(interval: number = SYNC_INTERVALS.STANDARD): void {
  stopBackgroundSync();
  syncTimer = setInterval(() => {
    if (navigator.onLine) {
      syncNow();
    }
  }, interval);

  window.addEventListener('online', handleOnline);
}

export function stopBackgroundSync(): void {
  if (syncTimer) {
    clearInterval(syncTimer);
    syncTimer = null;
  }
  window.removeEventListener('online', handleOnline);
}

async function handleOnline() {
  await syncNow();
}

export async function getSyncInfo() {
  const lastSync = await getLastSyncTimestamp();
  const pendingCount = await getQueueLength();

  return {
    lastSync: lastSync ? new Date(lastSync) : null,
    pendingCount,
    isSyncing,
  };
}

export function isSyncActive(): boolean {
  return isSyncing;
}
