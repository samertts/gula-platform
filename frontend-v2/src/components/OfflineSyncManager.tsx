import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { OfflineEngine, SyncStatus, SyncResult, SyncQueueItem } from '../lib/offline-engine';
import { FirebaseSyncEngine } from '../lib/firebase-sync';
import { Wifi, WifiOff, RefreshCw, AlertTriangle, CheckCircle, X, ChevronDown, ChevronUp, Clock, ArrowUpDown, Database } from 'lucide-react';

interface ConflictItem {
  id: string;
  collection: string;
  documentId: string;
  local: unknown;
  server: unknown;
  timestamp: number;
}

export const OfflineSyncManager: React.FC = () => {
  const engine = OfflineEngine.getInstance();
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({ status: 'idle', pending: 0, lastSync: 0 });
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isExpanded, setIsExpanded] = useState(false);
  const [pendingOps, setPendingOps] = useState<SyncQueueItem[]>([]);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastResult, setLastResult] = useState<SyncResult | null>(null);
  const [storageEstimate, setStorageEstimate] = useState<{ used: number; quota: number; percentage: number }>({ used: 0, quota: 0, percentage: 0 });

  useEffect(() => {
    const unsub = engine.onSyncStatusChange(setSyncStatus);
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    refreshPendingOps();
    refreshStorage();
    return () => {
      unsub();
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const refreshPendingOps = useCallback(async () => {
    const ops = await engine.getPendingOperations();
    setPendingOps(ops);
    const conflictOps = ops.filter(op => {
      const payload = op.payload as Record<string, unknown>;
      return payload?._conflict === true;
    });
    setConflicts(conflictOps.map(op => ({
      id: op.id,
      collection: op.collection,
      documentId: op.documentId,
      local: (op.payload as Record<string, unknown>)?.local,
      server: (op.payload as Record<string, unknown>)?.server,
      timestamp: op.timestamp,
    })));
  }, []);

  const refreshStorage = useCallback(async () => {
    const est = await engine.getStorageEstimate();
    setStorageEstimate(est);
  }, []);

  const handleSync = useCallback(async () => {
    if (isSyncing || !isOnline) return;
    setIsSyncing(true);
    const result = await engine.processQueue(async (item) => {
      const fbSync = FirebaseSyncEngine.getInstance();
      try {
        await fbSync.pushToAPI();
        return true;
      } catch {
        return false;
      }
    });
    setLastResult(result);
    await refreshPendingOps();
    await refreshStorage();
    setIsSyncing(false);
  }, [isSyncing, isOnline]);

  const handleResolveConflict = useCallback(async (conflictId: string, strategy: 'local' | 'server') => {
    const item = pendingOps.find(op => op.id === conflictId);
    if (!item) return;
    const payload = item.payload as Record<string, unknown>;
    if (strategy === 'local') {
      await engine.enqueue('update', item.collection, item.documentId, payload.local);
    } else {
      await engine.enqueue('update', item.collection, item.documentId, payload.server);
    }
    await engine.deleteDocument(item.collection as any, item.documentId);
    setConflicts(prev => prev.filter(c => c.id !== conflictId));
    await refreshPendingOps();
  }, [pendingOps]);

  const handlePurge = useCallback(async () => {
    const purged = await engine.purgeOldData();
    await refreshStorage();
    if (purged > 0) {
      console.log(`Purged ${purged} old records`);
    }
  }, []);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatTime = (ts: number): string => {
    if (!ts) return 'Never';
    return new Date(ts).toLocaleTimeString();
  };

  const getStatusColor = () => {
    if (syncStatus.status === 'syncing') return 'text-blue-500';
    if (syncStatus.status === 'error') return 'text-red-500';
    if (!isOnline) return 'text-amber-500';
    if (syncStatus.pending > 0) return 'text-amber-500';
    return 'text-green-500';
  };

  const getStatusIcon = () => {
    if (syncStatus.status === 'syncing') return <RefreshCw size={16} className="animate-spin" />;
    if (!isOnline) return <WifiOff size={16} />;
    if (syncStatus.pending > 0) return <Clock size={16} />;
    return <Wifi size={16} />;
  };

  if (!isOnline && syncStatus.pending === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden"
          >
            <div className="p-4 border-b border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-slate-800">Sync Manager</h3>
                <button onClick={() => setIsExpanded(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                  <X size={16} />
                </button>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <span className={`flex items-center gap-1.5 ${getStatusColor()}`}>
                  {getStatusIcon()}
                  <span className="font-medium capitalize">{syncStatus.status}</span>
                </span>
                <span className="text-slate-400">|</span>
                <span className="text-slate-500 flex items-center gap-1">
                  <Database size={12} />
                  {formatBytes(storageEstimate.used)} / {formatBytes(storageEstimate.quota)}
                </span>
              </div>
            </div>

            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Pending operations</span>
                <span className={`font-bold ${syncStatus.pending > 0 ? 'text-amber-600' : 'text-green-600'}`}>
                  {syncStatus.pending}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Last sync</span>
                <span className="text-slate-700 font-medium">{formatTime(syncStatus.lastSync)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Storage usage</span>
                <span className={`font-medium ${storageEstimate.percentage > 80 ? 'text-red-600' : storageEstimate.percentage > 50 ? 'text-amber-600' : 'text-green-600'}`}>
                  {storageEstimate.percentage.toFixed(1)}%
                </span>
              </div>

              {conflicts.length > 0 && (
                <div className="bg-red-50 rounded-xl p-3 border border-red-100">
                  <div className="flex items-center gap-2 text-red-700 text-xs font-bold mb-2">
                    <AlertTriangle size={14} />
                    {conflicts.length} conflict(s) require resolution
                  </div>
                  {conflicts.map(conflict => (
                    <div key={conflict.id} className="text-xs text-red-600 mb-1.5 last:mb-0 bg-white rounded-lg p-2 border border-red-100">
                      <div className="font-medium mb-1">{conflict.collection}/{conflict.documentId}</div>
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => handleResolveConflict(conflict.id, 'local')}
                          className="flex-1 px-2 py-1 bg-red-100 text-red-700 rounded-lg text-[10px] font-bold hover:bg-red-200 transition-colors"
                        >
                          Keep Local
                        </button>
                        <button
                          onClick={() => handleResolveConflict(conflict.id, 'server')}
                          className="flex-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-[10px] font-bold hover:bg-blue-200 transition-colors"
                        >
                          Keep Server
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {lastResult && (
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs">
                  <div className="font-medium text-slate-700 mb-1.5">Last sync result</div>
                  <div className="grid grid-cols-4 gap-2 text-center">
                    <div><span className="text-green-600 font-bold">{lastResult.success}</span><br /><span className="text-[10px] text-slate-400">Success</span></div>
                    <div><span className="text-red-600 font-bold">{lastResult.failed}</span><br /><span className="text-[10px] text-slate-400">Failed</span></div>
                    <div><span className="text-amber-600 font-bold">{lastResult.conflicts}</span><br /><span className="text-[10px] text-slate-400">Conflicts</span></div>
                    <div><span className="text-slate-600 font-bold">{lastResult.skipped}</span><br /><span className="text-[10px] text-slate-400">Skipped</span></div>
                  </div>
                </div>
              )}
            </div>

            <div className="p-3 border-t border-slate-100 bg-slate-50 flex gap-2">
              <button
                onClick={handleSync}
                disabled={isSyncing || !isOnline}
                className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <RefreshCw size={14} className={isSyncing ? 'animate-spin' : ''} />
                {isSyncing ? 'Syncing...' : 'Sync Now'}
              </button>
              <button
                onClick={handlePurge}
                className="px-3 py-2 bg-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-300 transition-colors"
              >
                Purge
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl shadow-lg border transition-all duration-200 ${isOnline ? 'bg-white border-slate-200' : 'bg-amber-50 border-amber-200'}`}
      >
        <span className={getStatusColor()}>{getStatusIcon()}</span>
        <span className="text-xs font-bold text-slate-700">
          {!isOnline ? 'Offline' : syncStatus.status === 'syncing' ? 'Syncing...' : `${syncStatus.pending} pending`}
        </span>
        {isExpanded ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronUp size={14} className="text-slate-400" />}
      </button>
    </div>
  );
};

export default OfflineSyncManager;
