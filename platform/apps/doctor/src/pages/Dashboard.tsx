import { useState } from 'react';
import { Card, CardHeader, CardBody, Badge, Button, LayoutContent, useRTL } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { AlertBanner } from '../components/AlertBanner';
import { PatientCard } from '../components/PatientCard';
import { useOfflineContext } from '../contexts/OfflineContext';

const MOCK_PATIENTS = [
  { id: '1', nationalId: '12345678901234', name: 'Ahmed Ali', nameAr: 'أحمد علي', dateOfBirth: '1985-03-15', gender: 'male' as const, bloodType: 'A+', allergies: ['Penicillin'], chronicConditions: ['Hypertension'], phone: '07701234567', labId: 'lab1', createdAt: '', updatedAt: '' },
  { id: '2', name: 'Sara Mohammed', nameAr: 'سارة محمد', dateOfBirth: '1992-07-22', gender: 'female' as const, bloodType: 'O-', allergies: [], chronicConditions: ['Asthma'], phone: '07707654321', labId: 'lab1', createdAt: '', updatedAt: '' },
  { id: '3', name: 'Hassan Ibrahim', nameAr: 'حسن إبراهيم', dateOfBirth: '1978-11-02', gender: 'male' as const, allergies: ['Sulfa'], chronicConditions: ['Diabetes Type 2', 'Hyperlipidemia'], phone: '07701112233', labId: 'lab1', createdAt: '', updatedAt: '' },
  { id: '4', name: 'Noor Khalid', nameAr: 'نور خالد', dateOfBirth: '2000-05-10', gender: 'female' as const, bloodType: 'AB+', allergies: [], chronicConditions: [], phone: '07704445566', labId: 'lab1', createdAt: '', updatedAt: '' },
  { id: '5', name: 'Omar Hassan', nameAr: 'عمر حسن', dateOfBirth: '1965-09-30', gender: 'male' as const, bloodType: 'B-', allergies: ['Aspirin', 'Ibuprofen'], chronicConditions: ['Hypertension', 'Diabetes Type 2', 'CKD'], phone: '07707778899', labId: 'lab1', createdAt: '', updatedAt: '' },
];

const MOCK_ALERTS = [
  { id: 'a1', type: 'critical' as const, title: 'Critical Lab Result', titleAr: 'نتيجة مختبر حرجة', message: 'Potassium: 6.8 mmol/L - Omar Hassan', messageAr: 'البوتاسيوم: 6.8 ملي مكافئ/لتر - عمر حسن', patientId: '5', patientName: 'Omar Hassan' },
  { id: 'a2', type: 'critical' as const, title: 'Drug Interaction Alert', titleAr: 'تنبيه تفاعل دوائي', message: 'Warfarin + Aspirin - Ahmed Ali', messageAr: 'وارفارين + أسبرين - أحمد علي', patientId: '1', patientName: 'Ahmed Ali' },
  { id: 'a3', type: 'warning' as const, title: 'Abnormal Vital Sign', titleAr: 'علامة حيوية غير طبيعية', message: 'BP 160/95 - Sara Mohammed', messageAr: 'ضغط الدم 160/95 - سارة محمد', patientId: '2', patientName: 'Sara Mohammed' },
];

export function Dashboard() {
  const { isRtl } = useRTL();
  const { user } = useAuth();
  const { isOffline, queueLength } = useOfflineContext();
  const [alerts, setAlerts] = useState(MOCK_ALERTS);
  const [patients] = useState(MOCK_PATIENTS);
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([]);

  const handleDismiss = (id: string) => {
    setDismissedAlerts(prev => [...prev, id]);
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  const visibleAlerts = alerts.filter(a => !dismissedAlerts.includes(a.id));
  const todayAppointments = 8;
  const pendingOrders = 12;
  const criticalResults = 3;

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? `مرحباً، ${user?.nameAr || 'الطبيب'}` : `Welcome, ${user?.name || 'Doctor'}`}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {new Date().toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
          {isOffline && (
            <Badge variant="danger" size="md">
              {isRtl ? 'غير متصل' : 'Offline'} ({queueLength})
            </Badge>
          )}
        </div>

        <AlertBanner alerts={visibleAlerts} onDismiss={handleDismiss} maxVisible={2} />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M3 10h18" /><path d="M8 2v4" /><path d="M16 2v4" /></svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{todayAppointments}</p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? 'مواعيد اليوم' : "Today's Appointments"}</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-warning-100 dark:bg-warning-900/30 flex items-center justify-center text-warning-600 dark:text-warning-400">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" /><path d="M14 2v6h6" /></svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{pendingOrders}</p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? 'الطلبات المعلقة' : 'Pending Orders'}</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-danger-100 dark:bg-danger-900/30 flex items-center justify-center text-danger-600 dark:text-danger-400">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10" /><path d="M12 8v4" /><path d="M12 16h.01" /></svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{criticalResults}</p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? 'نتائج حرجة' : 'Critical Results'}</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-success-100 dark:bg-success-900/30 flex items-center justify-center text-success-600 dark:text-success-400">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="8" r="4" /><path d="M20 21a8 8 0 10-16 0" /></svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{patients.length}</p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? 'مرضى اليوم' : "Today's Patients"}</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader
              title={isRtl ? 'قائمة الانتظار' : 'Patient Queue'}
              action={<Button variant="ghost" size="sm">{isRtl ? 'عرض الكل' : 'View All'}</Button>}
            />
            <CardBody>
              <div className="space-y-2">
                {patients.slice(0, 4).map((patient, i) => (
                  <PatientCard key={patient.id} patient={patient} compact onClick={() => {}} />
                ))}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title={isRtl ? 'الإحصائيات السريرية' : 'Clinical Stats'}
            />
            <CardBody>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600 dark:text-neutral-400">{isRtl ? 'مكتمل' : 'Completed'}</span>
                    <span className="font-bold">75%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-neutral-200 dark:bg-neutral-700">
                    <div className="h-full rounded-full bg-success-500" style={{ width: '75%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600 dark:text-neutral-400">{isRtl ? 'معلق' : 'Pending'}</span>
                    <span className="font-bold">15%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-neutral-200 dark:bg-neutral-700">
                    <div className="h-full rounded-full bg-warning-500" style={{ width: '15%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600 dark:text-neutral-400">{isRtl ? 'حرج' : 'Critical'}</span>
                    <span className="font-bold">10%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-neutral-200 dark:bg-neutral-700">
                    <div className="h-full rounded-full bg-danger-500" style={{ width: '10%' }} />
                  </div>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="text-center p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                  <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">18</p>
                  <p className="text-xs text-neutral-500">{isRtl ? 'تشخيص اليوم' : "Today's Diagnoses"}</p>
                </div>
                <div className="text-center p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
                  <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">9</p>
                  <p className="text-xs text-neutral-500">{isRtl ? 'وصفات اليوم' : "Today's Prescriptions"}</p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </LayoutContent>
  );
}
