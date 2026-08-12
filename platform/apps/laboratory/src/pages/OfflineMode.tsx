import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useOffline } from '@/contexts/OfflineContext';
import { offlineService } from '@/services/offline';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function OfflineMode() {
  const { isOnline, pendingCount, queue, processQueue, syncError } = useOffline();
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [drafts, setDrafts] = useState<{ id: string; updatedAt: string }[]>([]);

  useEffect(() => {
    if (isOnline) loadDrafts();
  }, [isOnline]);

  async function loadDrafts() {
    const d = await offlineService.listDrafts();
    setDrafts(d);
  }

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await offlineService.syncAll();
      setSyncStatus(result);
      await loadDrafts();
    } catch (e) {
      setSyncStatus({ error: (e as Error).message });
    }
    setSyncing(false);
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">الوضع غير المتصل</h1>
      <p className="text-sm text-neutral-500 -mt-5">إدارة المزامنة والبيانات غير المتصلة</p>

      <div className={cn(
        'p-8 rounded-3xl border-2 text-white',
        isOnline ? 'bg-success-500 border-success-600' : 'bg-warning-500 border-warning-600',
      )}>
        <div className="flex items-center gap-4">
          <div className={cn('w-6 h-6 rounded-full', isOnline ? 'bg-white/30' : 'bg-white/30 animate-pulse')}>
            {isOnline ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M5 12.55a11 11 0 0 1 14.08 0" /><path d="M1.42 9a16 16 0 0 1 21.16 0" /><path d="M8.53 16.11a6 6 0 0 1 6.95 0" /><line x1="12" y1="20" x2="12.01" y2="20" /></svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><line x1="1" y1="1" x2="23" y2="23" /><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" /><path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" /><path d="M10.71 5.05A16 16 0 0 1 22.56 9" /><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" /><path d="M8.53 16.11a6 6 0 0 1 6.95 0" /><line x1="12" y1="20" x2="12.01" y2="20" /></svg>
            )}
          </div>
          <div className="flex-1">
            <p className="text-lg font-black">{isOnline ? 'متصل بالإنترنت' : 'غير متصل بالإنترنت'}</p>
            <p className="text-sm opacity-90">
              {isOnline
                ? `النظام يعمل بشكل طبيعي. ${pendingCount} عملية معلقة.`
                : 'التطبيق يعمل في وضع عدم الاتصال. سيتم المزامنة تلقائياً عند توفر الاتصال.'}
            </p>
          </div>
          <span className={cn(
            'px-4 py-2 rounded-xl text-xs font-black',
            isOnline ? 'bg-white/20' : 'bg-white/20 animate-pulse',
          )}>
            {pendingCount} معلق
          </span>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <span className="font-bold">المزامنة</span>
            <button
              type="button"
              onClick={handleSync}
              disabled={syncing || !isOnline}
              className={cn(
                'px-4 py-2 rounded-xl font-bold text-xs transition-all',
                syncing ? 'bg-neutral-100 text-neutral-400' : 'bg-primary-500 text-white hover:bg-primary-600',
                'disabled:opacity-50',
              )}
            >
              {syncing ? (
                <span className="flex items-center gap-2">
                  <div className="w-3 h-3 border-2 border-primary-300 border-t-primary-600 rounded-full animate-spin" />
                  جاري المزامنة...
                </span>
              ) : 'مزامنة الآن'}
            </button>
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          {syncStatus && (
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-success-50 dark:bg-success-900/20 rounded-2xl text-center">
                <p className="text-2xl font-black text-success-600">{syncStatus.syncedItems || 0}</p>
                <p className="text-xs text-success-600 font-bold">تمت المزامنة</p>
              </div>
              <div className="p-4 bg-danger-50 dark:bg-danger-900/20 rounded-2xl text-center">
                <p className="text-2xl font-black text-danger-600">{syncStatus.failedItems || 0}</p>
                <p className="text-xs text-danger-600 font-bold">فشلت</p>
              </div>
              <div className="p-4 bg-neutral-100 dark:bg-neutral-700 rounded-2xl text-center">
                <p className="text-2xl font-black text-neutral-600">{syncStatus.pendingItems || 0}</p>
                <p className="text-xs text-neutral-600 font-bold">معلقة</p>
              </div>
            </div>
          )}

          {queue.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300">العمليات المعلقة ({queue.length})</p>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {queue.map((item, i) => (
                  <div key={item.id || i} className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl text-xs">
                    <div className="flex-1 min-w-0">
                      <p className="font-mono text-[10px] truncate">{item.url}</p>
                      <p className="text-neutral-400">{item.method} • محاولة {item.retryCount}/{item.maxRetries}</p>
                    </div>
                    {item.error && <span className="text-danger-500 text-[9px] mr-2">{item.error}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><span className="font-bold">المسودات غير المتصلة</span></CardHeader>
        <CardBody>
          {drafts.length === 0 ? (
            <p className="text-sm text-neutral-400 text-center py-4">لا توجد مسودات</p>
          ) : (
            <div className="space-y-2">
              {drafts.map(draft => (
                <div key={draft.id} className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl text-sm">
                  <span className="font-medium">{draft.id}</span>
                  <span className="text-xs text-neutral-400">{new Date(draft.updatedAt).toLocaleString('ar-IQ')}</span>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
