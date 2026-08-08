import { useState, useEffect, useCallback } from 'react';
import { getSyncInfo, syncNow, addSyncListener } from '../services/sync';

interface SyncState {
  lastSync: Date | null;
  pendingCount: number;
  isSyncing: boolean;
}

export function useSync() {
  const [state, setState] = useState<SyncState>({
    lastSync: null,
    pendingCount: 0,
    isSyncing: false,
  });

  useEffect(() => {
    const remove = addSyncListener((status, _error) => {
      if (status === 'syncing') {
        setState((prev) => ({ ...prev, isSyncing: true }));
      } else {
        getSyncInfo().then((info) =>
          setState({
            lastSync: info.lastSync,
            pendingCount: info.pendingCount,
            isSyncing: false,
          }),
        );
      }
    });

    getSyncInfo().then((info) =>
      setState({
        lastSync: info.lastSync,
        pendingCount: info.pendingCount,
        isSyncing: false,
      }),
    );

    const interval = setInterval(async () => {
      const info = await getSyncInfo();
      setState({
        lastSync: info.lastSync,
        pendingCount: info.pendingCount,
        isSyncing: info.isSyncing,
      });
    }, 10000);

    return () => {
      remove();
      clearInterval(interval);
    };
  }, []);

  const triggerSync = useCallback(async () => {
    setState((prev) => ({ ...prev, isSyncing: true }));
    await syncNow();
  }, []);

  return { ...state, triggerSync };
}
