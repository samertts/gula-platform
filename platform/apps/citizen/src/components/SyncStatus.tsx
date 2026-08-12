import { useSync } from '../hooks/useSync';

export function SyncStatus() {
  const { lastSync, pendingCount, isSyncing, triggerSync } = useSync();

  if (pendingCount === 0 && isSyncing === false) return null;

  return (
    <div className="px-4 py-2">
      <button
        onClick={triggerSync}
        disabled={isSyncing}
        className="w-full flex items-center justify-between px-4 py-2 bg-neutral-50 dark:bg-neutral-800 rounded-2xl text-xs"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`w-4 h-4 text-neutral-500 ${isSyncing ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span className="text-neutral-600 dark:text-neutral-400 font-medium">
            {isSyncing ? 'مزامنة...' : `${pendingCount} عنصر في انتظار المزامنة`}
          </span>
        </div>
        {lastSync && (
          <span className="text-neutral-400">
            {lastSync.toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </button>
    </div>
  );
}
