import { create } from 'zustand';
import type { SyncOperation, SyncConflict, SyncConfig, SyncStatus, NetworkStatus } from '../types';
import { DEFAULT_SYNC_CONFIG } from '../types';
import { getStorage } from '../db';

interface SyncState {
  queue: SyncOperation[];
  conflicts: SyncConflict[];
  config: SyncConfig;
  status: SyncStatus;
  network: NetworkStatus;
  lastSyncedAt: number | null;
  pendingCount: number;
  failedCount: number;

  enqueue: (op: Omit<SyncOperation, 'id' | 'timestamp' | 'retries' | 'status'>) => void;
  dequeue: (id: string) => void;
  markFailed: (id: string, error: string) => void;
  markCompleted: (id: string) => void;
  addConflict: (conflict: SyncConflict) => void;
  resolveConflict: (id: string, resolution: 'local' | 'remote' | 'merge') => void;
  setConfig: (config: Partial<SyncConfig>) => void;
  setStatus: (status: SyncStatus) => void;
  setNetwork: (network: NetworkStatus) => void;
  retryFailed: () => void;
  clearCompleted: () => void;
  getPending: () => SyncOperation[];
  getFailed: () => SyncOperation[];
}

export const useSyncQueue = create<SyncState>((set, get) => ({
  queue: [],
  conflicts: [],
  config: DEFAULT_SYNC_CONFIG,
  status: 'idle',
  network: navigator.onLine ? 'online' : 'offline',
  lastSyncedAt: null,
  pendingCount: 0,
  failedCount: 0,

  enqueue: (op) => {
    const operation: SyncOperation = {
      ...op,
      id: `sync-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      timestamp: Date.now(),
      retries: 0,
      status: 'pending',
    };
    set((state) => ({
      queue: [...state.queue, operation],
      pendingCount: state.pendingCount + 1,
    }));
  },

  dequeue: (id) => {
    set((state) => ({
      queue: state.queue.filter((op) => op.id !== id),
    }));
  },

  markFailed: (id, error) => {
    set((state) => ({
      queue: state.queue.map((op) =>
        op.id === id ? { ...op, status: 'failed' as const, error, retries: op.retries + 1 } : op
      ),
      failedCount: state.failedCount + 1,
      pendingCount: Math.max(0, state.pendingCount - 1),
    }));
  },

  markCompleted: (id) => {
    set((state) => ({
      queue: state.queue.map((op) =>
        op.id === id ? { ...op, status: 'completed' as const } : op
      ),
      pendingCount: Math.max(0, state.pendingCount - 1),
    }));
  },

  addConflict: (conflict) => {
    set((state) => ({
      conflicts: [...state.conflicts, conflict],
    }));
  },

  resolveConflict: (id, resolution) => {
    set((state) => ({
      conflicts: state.conflicts.map((c) =>
        c.id === id ? { ...c, resolution } : c
      ),
    }));
  },

  setConfig: (partial) => set((state) => ({ config: { ...state.config, ...partial } })),
  setStatus: (status) => set({ status }),
  setNetwork: (network) => set({ network }),
  retryFailed: () => {
    set((state) => ({
      queue: state.queue.map((op) =>
        op.status === 'failed' && op.retries < state.config.retryMaxAttempts
          ? { ...op, status: 'pending' as const, error: undefined }
          : op
      ),
      failedCount: 0,
    }));
  },
  clearCompleted: () => {
    set((state) => ({
      queue: state.queue.filter((op) => op.status !== 'completed'),
    }));
  },
  getPending: () => get().queue.filter((op) => op.status === 'pending'),
  getFailed: () => get().queue.filter((op) => op.status === 'failed'),
}));

export const processSyncQueue = async () => {
  const state = useSyncQueue.getState();
  if (state.network !== 'online' || state.status === 'syncing') return;
  if (state.pendingCount === 0) return;

  state.setStatus('syncing');
  const pending = state.getPending().slice(0, state.config.batchSize);

  for (const op of pending) {
    try {
      const storage = getStorage();
      if (op.type === 'delete') {
        await storage.delete(op.collection, op.entityId);
      } else if (op.data) {
        await storage.put({ id: op.entityId, collection: op.collection, data: op.data, createdAt: Date.now(), updatedAt: Date.now(), version: 1 });
        // In production, forward to API server here
      }
      state.markCompleted(op.id);
    } catch (error) {
      state.markFailed(op.id, String(error));
      if (op.retries + 1 >= state.config.retryMaxAttempts) {
        console.error(`[UAP Sync] Max retries reached for ${op.id}`);
      }
    }
  }

  state.setStatus('idle');
  useSyncQueue.setState({ lastSyncedAt: Date.now() });
};

let syncInterval: ReturnType<typeof setInterval> | null = null;

export const startSyncEngine = (intervalMs?: number) => {
  stopSyncEngine();
  const interval = intervalMs || useSyncQueue.getState().config.syncInterval;
  syncInterval = setInterval(processSyncQueue, interval);
};

export const stopSyncEngine = () => {
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = null;
  }
};

export const initNetworkMonitor = () => {
  const updateNetwork = () => {
    useSyncQueue.getState().setNetwork(navigator.onLine ? 'online' : 'offline');
  };
  window.addEventListener('online', updateNetwork);
  window.addEventListener('offline', updateNetwork);
  return () => {
    window.removeEventListener('online', updateNetwork);
    window.removeEventListener('offline', updateNetwork);
  };
};
