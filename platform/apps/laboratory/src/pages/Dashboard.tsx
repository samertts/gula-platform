import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { samplesService } from '@/services/samples';
import { resultsService } from '@/services/results';
import { qualityControlService } from '@/services/qualityControl';
import { analyzersService } from '@/services/analyzers';
import { inventoryService } from '@/services/inventory';
import { useWorklist } from '@/contexts/WorklistContext';
import { Card, CardBody, StatusIndicator } from '@gula/ui-platform';

export function Dashboard() {
  const { pendingCount, urgentCount } = useWorklist();
  const [stats, setStats] = useState({
    samplesToday: 0,
    pendingValidation: 0,
    criticalValues: 0,
    qcAlerts: 0,
    lowStock: 0,
    instrumentsOnline: 0,
    instrumentsTotal: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [sampleStats, resultStats, qcSummary, analyzerStats, invStats] = await Promise.all([
          samplesService.getStats({ dateFrom: new Date().toISOString().split('T')[0] }),
          resultsService.getStats({ dateFrom: new Date().toISOString().split('T')[0] }),
          qualityControlService.getSummary(),
          analyzersService.getDashboardStats(),
          inventoryService.getStats(),
        ]);

        setStats({
          samplesToday: sampleStats.total,
          pendingValidation: resultStats.pending,
          criticalValues: resultStats.critical,
          qcAlerts: qcSummary.warning + qcSummary.outOfControl,
          lowStock: invStats.lowStock + invStats.outOfStock,
          instrumentsOnline: analyzerStats.online,
          instrumentsTotal: analyzerStats.total,
        });
      } catch { /* use defaults */ }
      setLoading(false);
    }
    loadDashboard();
  }, []);

  const metrics = [
    {
      title: 'عينات اليوم',
      value: stats.samplesToday,
      subtitle: `${urgentCount} عينة عاجلة`,
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
      ),
      color: 'text-primary-600 bg-primary-50 dark:bg-primary-900/30',
      trend: '+12%',
    },
    {
      title: 'بانتظار التحقق',
      value: stats.pendingValidation,
      subtitle: `${stats.criticalValues} قيمة حرجة`,
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 11 12 14 22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
      ),
      color: 'text-warning-600 bg-warning-50 dark:bg-warning-900/30',
      trend: null,
    },
    {
      title: 'تنبيهات الجودة',
      value: stats.qcAlerts,
      subtitle: stats.qcAlerts > 0 ? 'يتطلب إجراءً' : 'تحت السيطرة',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
      ),
      color: stats.qcAlerts > 0 ? 'text-danger-600 bg-danger-50 dark:bg-danger-900/30' : 'text-success-600 bg-success-50 dark:bg-success-900/30',
      trend: null,
    },
    {
      title: 'المخزون المنخفض',
      value: stats.lowStock,
      subtitle: `${stats.instrumentsOnline}/${stats.instrumentsTotal} جهاز متصل`,
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></svg>
      ),
      color: stats.lowStock > 0 ? 'text-danger-600 bg-danger-50 dark:bg-danger-900/30' : 'text-success-600 bg-success-50 dark:bg-success-900/30',
      trend: null,
    },
  ];

  return (
    <div className="p-6 space-y-8 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">لوحة المعلومات</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">نظرة عامة على نشاط المختبر</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusIndicator status={loading ? 'idle' : 'online'} label={loading ? 'جاري التحميل...' : 'النظام نشط'} />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {metrics.map((m, i) => (
          <Card key={i} className="hover:shadow-lg transition-shadow">
            <CardBody>
              <div className="flex items-start justify-between mb-4">
                <div className={cn('p-3 rounded-2xl', m.color)}>{m.icon}</div>
                {m.trend && (
                  <span className="text-xs font-bold text-success-600 bg-success-50 dark:bg-success-900/30 dark:text-success-400 px-2 py-1 rounded-lg">
                    {m.trend}
                  </span>
                )}
              </div>
              <p className="text-3xl font-black text-neutral-900 dark:text-neutral-100 mb-1">{m.value}</p>
              <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300">{m.title}</p>
              <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-1">{m.subtitle}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardBody>
            <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 mb-4">حالة الجودة</h3>
            <QCStatusCard />
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 mb-4">حالة الأجهزة</h3>
            <InstrumentStatusSummary />
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardBody>
          <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 mb-4">العمل المعلق</h3>
          <PendingWorkSummary pendingCount={pendingCount} urgentCount={urgentCount} />
        </CardBody>
      </Card>
    </div>
  );
}

function QCStatusCard() {
  const [qcStats, setQcStats] = useState({ inControl: 0, warning: 0, outOfControl: 0, total: 0 });

  useEffect(() => {
    qualityControlService.getSummary().then(setQcStats).catch(() => {});
  }, []);

  const maxVal = Math.max(qcStats.inControl, qcStats.warning, qcStats.outOfControl, 1);

  return (
    <div className="space-y-4">
      {[
        { label: 'تحت السيطرة', value: qcStats.inControl, color: 'bg-success-500' },
        { label: 'تحذير', value: qcStats.warning, color: 'bg-warning-500' },
        { label: 'خارج السيطرة', value: qcStats.outOfControl, color: 'bg-danger-500' },
      ].map(item => (
        <div key={item.label} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-neutral-700 dark:text-neutral-300">{item.label}</span>
            <span className="font-bold text-neutral-900 dark:text-neutral-100">{item.value}</span>
          </div>
          <div className="h-2 bg-neutral-100 dark:bg-neutral-700 rounded-full overflow-hidden">
            <div className={cn('h-full rounded-full transition-all', item.color)} style={{ width: `${(item.value / maxVal) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function InstrumentStatusSummary() {
  const [instStats, setInstStats] = useState({ online: 0, offline: 0, maintenance: 0, error: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyzersService.getDashboardStats()
      .then(data => setInstStats(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-sm text-neutral-400">جاري التحميل...</div>;

  return (
    <div className="grid grid-cols-2 gap-4">
      {[
        { label: 'متصل', value: instStats.online, color: 'text-success-600', bg: 'bg-success-50 dark:bg-success-900/30' },
        { label: 'غير متصل', value: instStats.offline, color: 'text-neutral-600', bg: 'bg-neutral-100 dark:bg-neutral-700' },
        { label: 'صيانة', value: instStats.maintenance, color: 'text-warning-600', bg: 'bg-warning-50 dark:bg-warning-900/30' },
        { label: 'خطأ', value: instStats.error, color: instStats.error > 0 ? 'text-danger-600' : 'text-neutral-500', bg: instStats.error > 0 ? 'bg-danger-50 dark:bg-danger-900/30' : 'bg-neutral-100 dark:bg-neutral-700' },
      ].map(item => (
        <div key={item.label} className={cn('p-4 rounded-2xl text-center', item.bg)}>
          <p className={cn('text-2xl font-black', item.color)}>{item.value}</p>
          <p className={cn('text-xs font-bold mt-1', item.color)}>{item.label}</p>
        </div>
      ))}
    </div>
  );
}

function PendingWorkSummary({ pendingCount, urgentCount }: { pendingCount: number; urgentCount: number }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center text-primary-600 dark:text-primary-400">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" /></svg>
          </div>
          <div>
            <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">العمل المعلق</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">عينات غير مكتملة</p>
          </div>
        </div>
        <span className="text-2xl font-black text-primary-600 dark:text-primary-400">{pendingCount}</span>
      </div>

      <div className="flex items-center justify-between p-4 bg-warning-50 dark:bg-warning-900/20 rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-warning-100 dark:bg-warning-900/30 rounded-xl flex items-center justify-center text-warning-600 dark:text-warning-400">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
          </div>
          <div>
            <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">عينات عاجلة</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">تتطلب اهتماماً فورياً</p>
          </div>
        </div>
        <span className={cn('text-2xl font-black', urgentCount > 0 ? 'text-danger-600 dark:text-danger-400' : 'text-warning-600 dark:text-warning-400')}>
          {urgentCount}
        </span>
      </div>
    </div>
  );
}
