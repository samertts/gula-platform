export interface OfflineEntry<T = unknown> {
  id: string;
  collection: string;
  data: T;
  createdAt: number;
  updatedAt: number;
  syncedAt?: number;
  version: number;
  deleted?: boolean;
}

export interface SyncOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  collection: string;
  entityId: string;
  data?: unknown;
  timestamp: number;
  retries: number;
  status: 'pending' | 'processing' | 'failed' | 'completed';
  error?: string;
  priority: number;
}

export interface SyncConflict {
  id: string;
  collection: string;
  entityId: string;
  local: unknown;
  remote: unknown;
  timestamp: number;
  resolution?: 'local' | 'remote' | 'merge';
}

export interface SyncConfig {
  syncInterval: number;
  retryMaxAttempts: number;
  retryBackoffMs: number;
  batchSize: number;
  conflictStrategy: 'local-wins' | 'remote-wins' | 'last-write-wins' | 'manual';
}

export const DEFAULT_SYNC_CONFIG: SyncConfig = {
  syncInterval: 30000,
  retryMaxAttempts: 5,
  retryBackoffMs: 1000,
  batchSize: 50,
  conflictStrategy: 'last-write-wins',
};

export type ChangeCallback = (entry: OfflineEntry) => void;
export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline';
export type NetworkStatus = 'online' | 'offline' | 'poor';
