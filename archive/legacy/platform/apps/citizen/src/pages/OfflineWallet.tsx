import { useState, useEffect } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { getCachedHealthData, getCachedAppointments, getCachedNotifications, getCachedFamily, getCacheSize, clearAllCachedData, getEmergencyInfo } from '../services/offline';
import { getSyncInfo, syncNow } from '../services/sync';
import type { LabResult, Appointment, Notification, FamilyMember, EmergencyInfo as EmergencyInfoType } from '../types';

export function OfflineWallet() {
  const [cacheSize, setCacheSize] = useState('');
  const [syncInfo, setSyncInfo] = useState<{ lastSync: Date | null; pendingCount: number; isSyncing: boolean }>({
    lastSync: null, pendingCount: 0, isSyncing: false,
  });
  const [cachedCounts, setCachedCounts] = useState({ results: 0, appointments: 0, notifications: 0, family: 0 });
  const [hasEmergencyInfo, setHasEmergencyInfo] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    const [results, appointments, notifications, family, size, sync, emergency] = await Promise.all([
      getCachedHealthData(),
      getCachedAppointments(),
      getCachedNotifications(),
      getCachedFamily(),
      getCacheSize(),
      getSyncInfo(),
      getEmergencyInfo(),
    ]);
    setCachedCounts({
      results: results.length,
      appointments: appointments.length,
      notifications: notifications.length,
      family: family.length,
    });
    setCacheSize(size);
    setSyncInfo(sync);
    setHasEmergencyInfo(!!emergency);
  }

  async function handleSync() {
    setIsSyncing(true);
    await syncNow();
    await loadStats();
    setIsSyncing(false);
  }

  async function handleClearCache() {
    await clearAllCachedData();
    await loadStats();
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className={cn(
        'rounded-3xl p-6 mb-6 text-white',
        syncInfo.lastSync ? 'bg-gradient-to-br from-success-600 to-emerald-700' : 'bg-gradient-to-br from-warning-500 to-amber-600',
      )}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/70 mb-1">
              حالة المزامنة
            </p>
            <p className="text-lg font-black">
              {syncInfo.isSyncing ? 'جارٍ المزامنة...' : syncInfo.lastSync ? 'تمت المزامنة' : 'لم تتم المزامنة بعد'}
            </p>
          </div>
          <svg className="w-12 h-12 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </div>
        {syncInfo.lastSync && (
          <p className="text-xs text-white/70">
            آخر مزامنة: {syncInfo.lastSync.toLocaleDateString('ar-IQ', { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
        {syncInfo.pendingCount > 0 && (
          <p className="text-xs text-white/80 mt-1 font-bold">
            {syncInfo.pendingCount} عنصر في انتظار المزامنة
          </p>
        )}
      </div>

      <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 mb-6 border border-neutral-200 dark:border-neutral-700 shadow-sm">
        <h3 className="text-sm font-black text-neutral-900 dark:text-neutral-50 mb-4">البيانات المخزنة محلياً</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <span className="text-sm text-neutral-700 dark:text-neutral-300 font-medium">نتائج مختبر</span>
            </div>
            <span className="text-sm font-bold text-neutral-900 dark:text-neutral-50">{cachedCounts.results}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <rect x="3" y="4" width="18" height="18" rx="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 2v4M8 2v4M3 10h18" />
                </svg>
              </div>
              <span className="text-sm text-neutral-700 dark:text-neutral-300 font-medium">المواعيد</span>
            </div>
            <span className="text-sm font-bold text-neutral-900 dark:text-neutral-50">{cachedCounts.appointments}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <span className="text-sm text-neutral-700 dark:text-neutral-300 font-medium">الإشعارات</span>
            </div>
            <span className="text-sm font-bold text-neutral-900 dark:text-neutral-50">{cachedCounts.notifications}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <span className="text-sm text-neutral-700 dark:text-neutral-300 font-medium">أفراد العائلة</span>
            </div>
            <span className="text-sm font-bold text-neutral-900 dark:text-neutral-50">{cachedCounts.family}</span>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 mb-6 border border-neutral-200 dark:border-neutral-700 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-black text-neutral-900 dark:text-neutral-50">حجم التخزين المؤقت</h3>
            <p className="text-xs text-neutral-500 mt-0.5">{cacheSize}</p>
          </div>
          <div className={cn(
            'w-3 h-3 rounded-full',
            hasEmergencyInfo ? 'bg-success-500' : 'bg-neutral-300',
          )} title={hasEmergencyInfo ? 'معلومات الطوارئ محفوظة' : 'معلومات الطوارئ غير محفوظة'} />
        </div>
      </div>

      <div className="space-y-3">
        <Button
          fullWidth
          size="lg"
          loading={isSyncing}
          onClick={handleSync}
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          }
        >
          مزامنة الآن
        </Button>
        <Button
          fullWidth
          size="lg"
          variant="outline"
          onClick={handleClearCache}
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          }
        >
          مسح البيانات المخزنة
        </Button>
      </div>
    </div>
  );
}
