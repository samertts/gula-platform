import { useState, useEffect } from 'react';
import { useRTL } from '@gula/ui-platform';
import { useOfflineContext } from '../contexts/OfflineContext';

export function OfflineIndicator() {
  const { isOffline, syncStatus, triggerSync, queueLength } = useOfflineContext();
  const { isRtl } = useRTL();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (isOffline) {
      setVisible(true);
    } else if (syncStatus.pendingItems > 0) {
      setVisible(true);
    } else {
      const timer = setTimeout(() => setVisible(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOffline, syncStatus.pendingItems]);

  if (!visible && !isOffline && syncStatus.pendingItems === 0) return null;

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isOffline ? 'bg-danger-500' : syncStatus.isSyncing ? 'bg-primary-500' : 'bg-warning-500'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-white text-xs font-medium">
          {isOffline ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="1" y1="1" x2="23" y2="23" />
                <path d="M16.72 11.06A10.94 10.94 0 0119 12.55" />
                <path d="M5 12.55a10.94 10.94 0 015.17-2.39" />
                <path d="M10.71 5.05A16 16 0 0122.56 9" />
                <path d="M1.42 9a15.91 15.91 0 014.7-2.88" />
                <path d="M8.53 16.11a6 6 0 016.95 0" />
                <line x1="12" y1="20" x2="12.01" y2="20" />
              </svg>
              <span>{isRtl ? 'لا يوجد اتصال بالإنترنت' : 'You are offline'}</span>
            </>
          ) : syncStatus.isSyncing ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="animate-spin">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <span>{isRtl ? 'جاري المزامنة...' : 'Syncing...'}</span>
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10" />
                <polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
              </svg>
              <span>
                {isRtl
                  ? `${queueLength} عنصر في انتظار المزامنة`
                  : `${queueLength} items pending sync`}
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!isOffline && syncStatus.pendingItems > 0 && (
            <button
              onClick={triggerSync}
              disabled={syncStatus.isSyncing}
              className="text-white text-xs font-medium hover:underline disabled:opacity-50"
            >
              {syncStatus.isSyncing
                ? (isRtl ? 'جارٍ...' : 'Syncing...')
                : (isRtl ? 'مزامنة' : 'Sync now')}
            </button>
          )}
          {!isOffline && syncStatus.pendingItems === 0 && (
            <button onClick={() => setVisible(false)} className="text-white/80 hover:text-white">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
