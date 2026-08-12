import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useOffline } from '@/contexts/OfflineContext';
import { offlineService } from '@/services/offline';
import type { OfflineQueueItem } from '@/utils/types';

function OfflineMode() {
  const { isOnline, pendingCount, lastSync, syncAll } = useOffline();
  const [pendingItems, setPendingItems] = useState<OfflineQueueItem[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<{ success: number; failed: number } | null>(null);

  useEffect(() => {
    if (!isOnline) loadPending();
  }, [isOnline, pendingCount]);

  const loadPending = async () => {
    const items = await offlineService.getPending();
    setPendingItems(items);
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    let success = 0;
    let failed = 0;
    try {
      await syncAll();
      const remaining = await offlineService.getPending();
      success = pendingItems.length - remaining.length;
      failed = remaining.length;
      setPendingItems(remaining);
      setSyncResult({ success, failed });
    } catch {
      setSyncResult({ success: 0, failed: pendingItems.length });
    } finally {
      setSyncing(false);
    }
  };

  const handleClearSynced = async () => {
    await offlineService.clearSynced();
    loadPending();
  };

  const handleClearAll = async () => {
    if (window.confirm('هل أنت متأكد من حذف جميع العناصر؟')) {
      await offlineService.clearAll();
      setPendingItems([]);
    }
  };

  const getItemTypeLabel = (type: string) => {
    const labels: Record<string, string> = { vitals: 'علامات حيوية', medication: 'دواء', task: 'مهمة', assessment: 'تقييم' };
    return labels[type] || type;
  };

  const getItemActionLabel = (action: string) => {
    return action === 'create' ? 'إنشاء' : 'تحديث';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">وضع عدم الاتصال</h1>
        <div className={cn(
          'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-xl font-bold',
          isOnline ? 'bg-success-50 dark:bg-success-900/20 text-success-600 dark:text-success-400' : 'bg-warning-50 dark:bg-warning-900/20 text-warning-600 dark:text-warning-400',
        )}>
          <span className={cn('w-2 h-2 rounded-full', isOnline ? 'bg-success-500' : 'bg-warning-500 animate-pulse')} />
          {isOnline ? 'متصل' : 'غير متصل'}
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'الحالة', value: isOnline ? 'متصل' : 'غير متصل', color: isOnline ? 'text-success-600' : 'text-warning-600' },
            { label: 'العناصر المعلقة', value: pendingCount, color: 'text-primary-600' },
            { label: 'آخر مزامنة', value: lastSync ? lastSync.toLocaleTimeString('ar-IQ') : '--', color: 'text-neutral-600' },
            { label: 'التخزين المؤقت', value: `${pendingItems.length} عنصر`, color: 'text-neutral-600' },
          ].map(s => (
            <div key={s.label} className="bg-neutral-50 dark:bg-neutral-700/50 p-3 rounded-xl text-center">
              <p className={cn('text-lg font-black', s.color)}>{s.value}</p>
              <p className="text-[10px] text-neutral-500 dark:text-neutral-400 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {syncResult && (
        <div className={cn('p-4 rounded-2xl border', syncResult.failed === 0 ? 'bg-success-50 dark:bg-success-900/20 border-success-200 dark:border-success-800' : 'bg-warning-50 dark:bg-warning-900/20 border-warning-200 dark:border-warning-800')}>
          <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300">نتيجة المزامنة</p>
          <div className="flex gap-4 mt-1 text-xs">
            <span className="text-success-600">تمت المزامنة: {syncResult.success}</span>
            {syncResult.failed > 0 && <span className="text-danger-600">فشل: {syncResult.failed}</span>}
          </div>
        </div>
      )}

      {!isOnline && (
        <div className="bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 p-4 rounded-2xl">
          <div className="flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <p className="font-bold text-sm text-warning-700 dark:text-warning-400">أنت في وضع عدم الاتصال</p>
              <p className="text-xs text-warning-600 dark:text-warning-500 mt-1">سيتم حفظ البيانات محلياً ومزامنتها تلقائياً عند استعادة الاتصال</p>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleSync}
          disabled={syncing || !isOnline || pendingCount === 0}
          className={cn(
            'flex-1 py-3 rounded-2xl font-bold text-sm transition-all',
            'bg-primary-500 text-white hover:bg-primary-600',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {syncing ? (
            <span className="inline-flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              جاري المزامنة...
            </span>
          ) : `مزامنة (${pendingCount})`}
        </button>
        {pendingItems.some(i => i.synced) && (
          <button onClick={handleClearSynced} className="px-4 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 rounded-2xl font-bold text-sm hover:bg-neutral-200 transition-colors">
            مسح المكتمل
          </button>
        )}
        <button onClick={handleClearAll} className="px-4 py-3 bg-danger-50 dark:bg-danger-900/20 text-danger-600 dark:text-danger-400 rounded-2xl font-bold text-sm hover:bg-danger-100 transition-colors">
          حذف الكل
        </button>
      </div>

      <div className="space-y-3">
        <h2 className="font-bold text-sm text-neutral-700 dark:text-neutral-300">قائمة الانتظار ({pendingItems.length})</h2>
        {pendingItems.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700">
            <p className="text-4xl mb-3">✅</p>
            <p className="text-sm font-bold text-neutral-500 dark:text-neutral-400">لا توجد عناصر في قائمة الانتظار</p>
            <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-1">جميع البيانات متزامنة</p>
          </div>
        ) : (
          pendingItems.map(item => (
            <div key={item.id} className={cn(
              'bg-white dark:bg-neutral-800 rounded-2xl border p-4',
              item.synced ? 'border-success-200 dark:border-success-800' : 'border-neutral-200 dark:border-neutral-700',
            )}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-bold text-sm text-neutral-900 dark:text-neutral-100">{getItemTypeLabel(item.type)}</p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">{getItemActionLabel(item.action)}</p>
                </div>
                <span className={cn('text-[10px] px-2 py-0.5 rounded-lg font-bold', item.synced ? 'bg-success-100 text-success-600' : 'bg-warning-100 text-warning-600')}>
                  {item.synced ? 'تمت المزامنة' : 'معلق'}
                </span>
              </div>
              <p className="text-[10px] text-neutral-400 dark:text-neutral-500 mt-2">
                {new Date(item.createdAt).toLocaleString('ar-IQ')}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default OfflineMode;
