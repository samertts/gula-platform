import type { SyncConflict } from '../types';

export type ResolutionStrategy = 'local-wins' | 'remote-wins' | 'last-write-wins' | 'manual';

export interface ConflictResolver {
  resolve: (conflict: SyncConflict, strategy: ResolutionStrategy) => unknown;
  merge: (local: unknown, remote: unknown) => unknown;
}

export const defaultConflictResolver: ConflictResolver = {
  resolve: (conflict: SyncConflict, strategy: ResolutionStrategy) => {
    switch (strategy) {
      case 'local-wins':
        return conflict.local;
      case 'remote-wins':
        return conflict.remote;
      case 'last-write-wins': {
        const localTs = (conflict.local as any)?.updatedAt ?? 0;
        const remoteTs = (conflict.remote as any)?.updatedAt ?? 0;
        return localTs >= remoteTs ? conflict.local : conflict.remote;
      }
      case 'manual':
      default:
        return null;
    }
  },

  merge: (local: unknown, remote: unknown) => {
    if (typeof local !== 'object' || typeof remote !== 'object' || !local || !remote) {
      return remote;
    }
    const merged = { ...(local as Record<string, unknown>) };
    const remoteObj = remote as Record<string, unknown>;
    for (const key of Object.keys(remoteObj)) {
      if (key === 'version' || key === 'updatedAt') continue;
      if (remoteObj[key] !== undefined && remoteObj[key] !== null) {
        merged[key] = remoteObj[key];
      }
    }
    return merged;
  },
};
