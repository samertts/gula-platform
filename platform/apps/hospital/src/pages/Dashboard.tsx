import { useEffect, useMemo, useState } from 'react';
import { Card, CardHeader, CardBody, Badge, Button, LayoutContent, useRTL } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { getHospitalDashboard, type HospitalDashboardResponse } from '../services/dashboard';

export function Dashboard() {
  const { isRtl } = useRTL();
  const { user } = useAuth();
  const [dateStr, setDateStr] = useState('');
  const [data, setData] = useState<HospitalDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDateStr(new Date().toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    }));
  }, [isRtl]);

  const loadDashboard = async () => {
    const hospitalId = Number(user?.hospitalId);
    if (!Number.isInteger(hospitalId) || hospitalId <= 0) {
      setError(isRtl ? 'معرّف المستشفى غير متوفر في جلسة المستخدم.' : 'The authenticated hospital identifier is missing.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      setData(await getHospitalDashboard(hospitalId));
    } catch (cause) {
      setData(null);
      setError(cause instanceof Error ? cause.message : (isRtl ? 'تعذر تحميل لوحة المستشفى.' : 'Unable to load the hospital dashboard.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboard();
  }, [user?.hospitalId, isRtl]);

  const occupancy = useMemo(() => {
    if (!data || data.beds.total <= 0) return 0;
    return Math.round((data.beds.occupied / data.beds.total) * 100);
  }, [data]);

  const metrics = data ? [
    { label: isRtl ? 'الأقسام' : 'Departments', value: data.departments, tone: 'primary' },
    { label: isRtl ? 'العيادات' : 'Clinics', value: data.clinics, tone: 'success' },
    { label: isRtl ? 'الغرف' : 'Rooms', value: data.rooms, tone: 'info' },
    { label: isRtl ? 'الأسرة' : 'Beds', value: `${data.beds.occupied}/${data.beds.total}`, tone: 'danger' },
    { label: isRtl ? 'المعدات التشغيلية' : 'Operational equipment', value: `${data.equipment.operational}/${data.equipment.total}`, tone: 'warning' },
    { label: isRtl ? 'غرف العمليات المتاحة' : 'Available operating theatres', value: `${data.operation_theaters.available}/${data.operation_theaters.total}`, tone: 'primary' },
  ] : [];

  return (
    <LayoutContent>
      <div className="space-y-6" aria-busy={isLoading}>
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? `مرحباً، ${user?.nameAr || 'المدير'}` : `Welcome, ${user?.name || 'Admin'}`}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">{dateStr}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={error ? 'danger' : isLoading ? 'warning' : 'success'} size="lg">
              {error ? (isRtl ? 'غير متاح' : 'Unavailable') : isLoading ? (isRtl ? 'جاري التحميل' : 'Loading') : `${isRtl ? 'الإشغال' : 'Occupancy'}: ${occupancy}%`}
            </Badge>
            <Button variant="outline" size="sm" onClick={() => void loadDashboard()} loading={isLoading}>
              {isRtl ? 'تحديث' : 'Refresh'}
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-danger-200 bg-danger-50 p-4 text-sm text-danger-700 dark:border-danger-800 dark:bg-danger-900/20 dark:text-danger-300" role="alert">
            <div className="flex items-center justify-between gap-3">
              <span>{error}</span>
              <Button variant="outline" size="sm" onClick={() => void loadDashboard()} disabled={isLoading}>
                {isRtl ? 'إعادة المحاولة' : 'Retry'}
              </Button>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" role="status" aria-label={isRtl ? 'جاري تحميل مؤشرات المستشفى' : 'Loading hospital metrics'}>
            {[1, 2, 3, 4, 5, 6].map((item) => <div key={item} className="h-28 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />)}
          </div>
        ) : !data ? (
          <Card><CardBody><p className="py-8 text-center text-sm text-neutral-500">{isRtl ? 'لا توجد بيانات لوحة متاحة من الخادم.' : 'No dashboard data was returned by the backend.'}</p></CardBody></Card>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {metrics.map((metric) => (
                <Card key={metric.label} variant="elevated" padding="md">
                  <CardBody>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">{metric.label}</p>
                    <p className="text-2xl font-bold mt-2 text-neutral-900 dark:text-neutral-50">{metric.value}</p>
                    <p className="text-xs text-neutral-400 mt-2">{isRtl ? 'من عقد Backend الحالي' : 'From the current backend contract'}</p>
                  </CardBody>
                </Card>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader title={isRtl ? 'إشغال الأسرة' : 'Bed occupancy'} />
                <CardBody>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-neutral-600 dark:text-neutral-400">{isRtl ? 'المشغولة / الإجمالي' : 'Occupied / total'}</span>
                    <span className="font-bold">{data.beds.occupied} / {data.beds.total}</span>
                  </div>
                  <div className="w-full h-3 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-primary-500 transition-all duration-300" style={{ width: `${occupancy}%` }} />
                  </div>
                  <p className="text-xs text-neutral-500 mt-3">{isRtl ? 'المؤشر محسوب من أرقام الأسرة التي أعادها الخادم، ولا يستبدل نظام الطوارئ أو قرار التخصيص.' : 'Calculated from backend bed counts; it does not replace emergency or bed-assignment workflows.'}</p>
                </CardBody>
              </Card>
              <Card>
                <CardHeader title={isRtl ? 'حدود البيانات الحالية' : 'Current data boundary'} />
                <CardBody>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-6">
                    {isRtl ? 'تعرض هذه اللوحة مؤشرات المستشفى التي يدعمها endpoint الحالي فقط. لا تُعرض تنبيهات أو مالية أو جداول موظفين ما لم يقدّم Backend عقداً مصادقاً لها.' : 'This view displays only hospital metrics supported by the current authenticated endpoint. Alerts, finance, and staffing are not fabricated when their backend contracts are unavailable.'}
                  </p>
                </CardBody>
              </Card>
            </div>
          </>
        )}
      </div>
    </LayoutContent>
  );
}
