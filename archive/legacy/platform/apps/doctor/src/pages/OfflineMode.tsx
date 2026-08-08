import { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { useOfflineContext } from '../contexts/OfflineContext';

export function OfflineMode() {
  const { isRtl } = useRTL();
  const { isOnline, isOffline, syncStatus, triggerSync, queueLength } = useOfflineContext();
  const [timeSinceLastSync, setTimeSinceLastSync] = useState('');

  useEffect(() => {
    const update = () => {
      if (syncStatus.lastSync) {
        const diff = Date.now() - new Date(syncStatus.lastSync).getTime();
        const mins = Math.floor(diff / 60000);
        setTimeSinceLastSync(mins < 1 ? (isRtl ? 'أقل من دقيقة' : '< 1 min') : `${mins} ${isRtl ? 'دقيقة' : 'min'}`);
      } else {
        setTimeSinceLastSync(isRtl ? 'لم تتم المزامنة بعد' : 'Never synced');
      }
    };
    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, [syncStatus.lastSync, isRtl]);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'الوضع غير المتصل' : 'Offline Mode'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'إدارة المزامنة والبيانات غير المتصلة' : 'Manage sync and offline data'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card variant="elevated">
            <CardHeader
              title={isRtl ? 'حالة الاتصال' : 'Connection Status'}
              action={
                <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-success-500' : 'bg-danger-500'}`} />
              }
            />
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    {isRtl ? 'حالة الشبكة' : 'Network Status'}
                  </span>
                  <Badge variant={isOnline ? 'success' : 'danger'}>
                    {isOnline ? (isRtl ? 'متصل' : 'Online') : (isRtl ? 'غير متصل' : 'Offline')}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    {isRtl ? 'المزامنة التلقائية' : 'Auto-sync'}
                  </span>
                  <Badge variant={syncStatus.isSyncing ? 'info' : isOnline ? 'success' : 'default'}>
                    {syncStatus.isSyncing ? (isRtl ? 'جارٍ' : 'Syncing') : isOnline ? (isRtl ? 'نشط' : 'Active') : (isRtl ? 'معلق' : 'Paused')}
                  </Badge>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card variant="elevated">
            <CardHeader
              title={isRtl ? 'المزامنة' : 'Sync Status'}
              action={
                <Button variant="primary" size="sm" onClick={triggerSync} loading={syncStatus.isSyncing} disabled={isOffline}>
                  {isRtl ? 'مزامنة' : 'Sync'}
                </Button>
              }
            />
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    {isRtl ? 'آخر مزامنة' : 'Last Sync'}
                  </span>
                  <span className="text-sm font-medium">{timeSinceLastSync}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    {isRtl ? 'العناصر المعلقة' : 'Pending Items'}
                  </span>
                  <span className={`text-sm font-bold ${queueLength > 0 ? 'text-warning-600' : 'text-success-600'}`}>
                    {queueLength}
                  </span>
                </div>
                {syncStatus.errors && syncStatus.errors.length > 0 && (
                  <div className="p-3 rounded-xl bg-danger-50 dark:bg-danger-950 border border-danger-200 dark:border-danger-900">
                    <p className="text-xs text-danger-700 dark:text-danger-400">
                      {isRtl ? 'أخطاء المزامنة' : 'Sync Errors'}:
                    </p>
                    {syncStatus.errors.map((err, i) => (
                      <p key={i} className="text-xs text-danger-600 mt-1">{err}</p>
                    ))}
                  </div>
                )}
              </div>
            </CardBody>
          </Card>
        </div>

        <Card>
          <CardHeader title={isRtl ? 'التخزين المحلي' : 'Local Storage'} />
          <CardBody>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                <span className="text-sm">{isRtl ? 'المرضى المخزنين محلياً' : 'Cached Patients'}</span>
                <span className="text-sm font-bold">12</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                <span className="text-sm">{isRtl ? 'النتائج المخزنة' : 'Cached Results'}</span>
                <span className="text-sm font-bold">45</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                <span className="text-sm">{isRtl ? 'الطلبات المعلقة' : 'Pending Requests'}</span>
                <span className="text-sm font-bold">{queueLength}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                <span className="text-sm">{isRtl ? 'حجم التخزين' : 'Storage Used'}</span>
                <span className="text-sm font-bold">~2.3 MB</span>
              </div>
            </div>
          </CardBody>
        </Card>

        <div className="p-4 rounded-xl bg-info-50 dark:bg-info-950 border border-info-200 dark:border-info-900">
          <p className="text-sm text-info-700 dark:text-info-400">
            {isRtl
              ? 'في الوضع غير المتصل، يمكنك الاستمرار في عرض بيانات المرضى المخزنة وإنشاء طلبات جديدة. سيتم مزامنة جميع التغييرات تلقائياً عند استعادة الاتصال.'
              : 'In offline mode, you can continue viewing cached patient data and creating new requests. All changes will sync automatically when connection is restored.'}
          </p>
        </div>
      </div>
    </LayoutContent>
  );
}
