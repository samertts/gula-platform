import { useCallback, useEffect, useState } from 'react';
import { Card, CardHeader, CardBody, Badge, Button, LayoutContent, useRTL } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { AlertBanner } from '../components/AlertBanner';
import { PatientCard } from '../components/PatientCard';
import { useOfflineContext } from '../contexts/OfflineContext';
import { formatCriticalTests, getDoctorCriticalAlerts, getDoctorRecentPatients, type CriticalAlertRecord } from '../services/dashboard';
import type { Patient } from '../services/patient';

interface DashboardError {
  message: string;
}

export function Dashboard() {
  const { isRtl } = useRTL();
  const { user } = useAuth();
  const { isOffline, queueLength } = useOfflineContext();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [criticalAlerts, setCriticalAlerts] = useState<CriticalAlertRecord[]>([]);
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<DashboardError | null>(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [patientResponse, alertResponse] = await Promise.all([
        getDoctorRecentPatients(1, 20),
        getDoctorCriticalAlerts(20),
      ]);
      setPatients(patientResponse.patients);
      setCriticalAlerts(alertResponse.alerts);
      setDismissedAlerts([]);
    } catch (cause) {
      setError({
        message: cause instanceof Error
          ? cause.message
          : (isRtl ? 'تعذر تحميل بيانات لوحة الطبيب.' : 'Unable to load the doctor dashboard.'),
      });
    } finally {
      setIsLoading(false);
    }
  }, [isRtl]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const visibleAlerts = criticalAlerts
    .filter((alert) => !dismissedAlerts.includes(String(alert.id)))
    .map((alert) => ({
      id: String(alert.id),
      type: 'critical' as const,
      title: 'Critical laboratory result',
      titleAr: 'نتيجة مختبر حرجة',
      message: `${formatCriticalTests(alert.critical_tests)} — order #${alert.order_id ?? '—'}`,
      messageAr: `${formatCriticalTests(alert.critical_tests)} — الطلب ${alert.order_id ?? '—'}`,
    }));

  const handleDismiss = (id: string) => {
    setDismissedAlerts((previous) => [...previous, id]);
  };

  return (
    <LayoutContent>
      <div className="space-y-6" aria-busy={isLoading}>
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? `مرحباً، ${user?.nameAr || 'الطبيب'}` : `Welcome, ${user?.name || 'Doctor'}`}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {new Date().toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isOffline && (
              <Badge variant="danger" size="md">
                {isRtl ? 'غير متصل' : 'Offline'} ({queueLength})
              </Badge>
            )}
            <Button variant="outline" size="sm" onClick={() => void loadDashboard()} loading={isLoading}>
              {isRtl ? 'تحديث' : 'Refresh'}
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-danger-200 bg-danger-50 p-4 text-sm text-danger-700 dark:border-danger-800 dark:bg-danger-900/20 dark:text-danger-300" role="alert">
            <div className="flex items-center justify-between gap-3">
              <span>{error.message}</span>
              <Button variant="outline" size="sm" onClick={() => void loadDashboard()} disabled={isLoading}>
                {isRtl ? 'إعادة المحاولة' : 'Retry'}
              </Button>
            </div>
          </div>
        )}

        <AlertBanner alerts={visibleAlerts} onDismiss={handleDismiss} maxVisible={2} />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="9" cy="8" r="4" /><path d="M17 11a3 3 0 100-6" /><path d="M3 21a6 6 0 0112 0" /><path d="M16 15a5 5 0 015 5" /></svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{isLoading ? '—' : patients.length}</p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? 'مرضى حديثون من الخادم' : 'Recent patients from backend'}</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-danger-100 dark:bg-danger-900/30 flex items-center justify-center text-danger-600 dark:text-danger-400" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10" /><path d="M12 8v4" /><path d="M12 16h.01" /></svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{isLoading ? '—' : criticalAlerts.length}</p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? 'تنبيهات حرجة من الخادم' : 'Critical alerts from backend'}</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-warning-100 dark:bg-warning-900/30 flex items-center justify-center text-warning-600 dark:text-warning-400" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 2v20M2 12h20" /></svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{queueLength}</p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? 'عمليات بانتظار المزامنة' : 'Operations awaiting sync'}</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader
              title={isRtl ? 'المرضى الحديثون' : 'Recent Patients'}
              action={<Button variant="ghost" size="sm" onClick={() => void loadDashboard()}>{isRtl ? 'تحديث' : 'Refresh'}</Button>}
            />
            <CardBody>
              {isLoading ? (
                <div className="space-y-3" role="status" aria-label={isRtl ? 'جاري التحميل' : 'Loading'}>
                  {[1, 2, 3].map((item) => <div key={item} className="h-16 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />)}
                </div>
              ) : patients.length === 0 ? (
                <p className="text-sm text-neutral-500 text-center py-8">{isRtl ? 'لا توجد سجلات مرضى حديثة.' : 'No recent patients were returned by the backend.'}</p>
              ) : (
                <div className="space-y-2">
                  {patients.slice(0, 4).map((patient) => (
                    <PatientCard key={patient.id} patient={patient} compact onClick={() => {}} />
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title={isRtl ? 'حالة البيانات الحية' : 'Live Data Status'} />
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-xl bg-neutral-50 p-4 dark:bg-neutral-900">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">{isRtl ? 'مصدر لوحة الطبيب' : 'Doctor dashboard source'}</span>
                  <Badge variant={error ? 'danger' : isOffline ? 'warning' : 'success'} size="sm">
                    {error ? (isRtl ? 'تعذر التحميل' : 'Unavailable') : isOffline ? (isRtl ? 'بيانات غير متصلة' : 'Degraded') : (isRtl ? 'متصل بالخادم' : 'Backend connected')}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                    <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">{patients.length}</p>
                    <p className="text-xs text-neutral-500">{isRtl ? 'سجلات معروضة' : 'Records displayed'}</p>
                  </div>
                  <div className="text-center p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                    <p className="text-2xl font-bold text-danger-600 dark:text-danger-400">{criticalAlerts.length}</p>
                    <p className="text-xs text-neutral-500">{isRtl ? 'تنبيهات حرجة' : 'Critical alerts'}</p>
                  </div>
                </div>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">
                  {isRtl ? 'لا تعرض هذه اللوحة بيانات اصطناعية. عند تعذر الخادم تظهر حالة فارغة أو خطأ قابلة لإعادة المحاولة.' : 'This dashboard never substitutes synthetic clinical data when the backend is unavailable.'}
                </p>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </LayoutContent>
  );
}
