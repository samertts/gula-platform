import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn, useRTL } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { useOffline } from '@/contexts/OfflineContext';
import { patientsService } from '@/services/patients';
import { tasksService } from '@/services/tasks';
import { medicationsService } from '@/services/medications';
import { ROUTES, getShiftArabic } from '@/utils/routes';
import type { Patient, NursingTask, Medication } from '@/utils/types';

interface DashboardCounts {
  patients: number;
  tasks: { urgent: number; high: number; medium: number; low: number };
  medications: number;
  overdue: number;
}

function Dashboard() {
  const navigate = useNavigate();
  const { user } = useNurse();
  const { isOnline, pendingCount } = useOffline();
  const { isRtl } = useRTL();

  const [counts, setCounts] = useState<DashboardCounts | null>(null);
  const [criticalPatients, setCriticalPatients] = useState<Patient[]>([]);
  const [overdueTasks, setOverdueTasks] = useState<NursingTask[]>([]);
  const [upcomingMeds, setUpcomingMeds] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, [user?.ward]);

  const loadDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const ward = user?.ward;
      const [patientList, priorityCount, overdueList, medList] = await Promise.all([
        patientsService.getList(ward),
        tasksService.getPriorityCount(ward),
        tasksService.getOverdue(ward),
        medicationsService.getScheduled(ward),
      ]);
      setCounts({
        patients: patientList.length,
        tasks: priorityCount,
        medications: medList.length,
        overdue: overdueList.length,
      });
      setCriticalPatients(patientList.filter(p => p.fallRisk || p.isolation));
      setOverdueTasks(overdueList.slice(0, 5));
      setUpcomingMeds(medList.filter(m => m.status === 'scheduled').slice(0, 5));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-3">جاري تحميل البيانات...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-sm">
          <div className="w-16 h-16 bg-danger-50 dark:bg-danger-900/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-danger-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><path d="M12 8v4m0 4h.01" />
            </svg>
          </div>
          <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">خطأ في التحميل</p>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-4">{error}</p>
          <button onClick={loadDashboard} className="px-4 py-2 bg-primary-500 text-white rounded-xl font-bold text-xs hover:bg-primary-600 transition-colors">
            إعادة المحاولة
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" dir={isRtl ? 'rtl' : 'ltr'}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">لوحة المعلومات</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">
            مرحباً {user?.name} • {user?.ward ? `${getShiftArabic(user.shift)} • ` : ''}الجناح: {user?.ward || 'غير محدد'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isOnline && (
            <span className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-warning-50 dark:bg-warning-900/20 text-warning-600 dark:text-warning-400 rounded-xl font-bold border border-warning-200 dark:border-warning-800">
              <span className="w-2 h-2 bg-warning-500 rounded-full animate-pulse" />
              غير متصل ({pendingCount})
            </span>
          )}
          <button onClick={loadDashboard} className="p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-xl transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'المرضى', value: counts?.patients ?? 0, icon: '👥', color: 'bg-primary-500', href: ROUTES.WARD },
          { label: 'مهام عاجلة', value: counts?.tasks.urgent ?? 0, icon: '🔴', color: 'bg-danger-500', href: ROUTES.TASKS },
          { label: 'الأدوية المجدولة', value: counts?.medications ?? 0, icon: '💊', color: 'bg-success-500', href: ROUTES.MEDICATIONS },
          { label: 'مهام متأخرة', value: counts?.overdue ?? 0, icon: '⚠️', color: 'bg-warning-500', href: ROUTES.TASKS },
        ].map(card => (
          <button
            key={card.label}
            onClick={() => navigate(card.href)}
            className="bg-white dark:bg-neutral-800 rounded-2xl p-4 border border-neutral-200 dark:border-neutral-700 hover:shadow-md transition-all text-right"
          >
            <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center text-lg mb-3', card.color)}>
              {card.icon}
            </div>
            <p className="text-2xl font-black text-neutral-900 dark:text-neutral-100">{card.value}</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{card.label}</p>
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-neutral-900 dark:text-neutral-100">المهام المتأخرة</h2>
            <button onClick={() => navigate(ROUTES.TASKS)} className="text-xs text-primary-500 font-bold hover:text-primary-600">عرض الكل</button>
          </div>
          {overdueTasks.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-3xl mb-2">✅</p>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">لا توجد مهام متأخرة</p>
            </div>
          ) : (
            <div className="space-y-2">
              {overdueTasks.map(task => (
                <div key={task.id} className="flex items-center gap-3 p-3 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl">
                  <span className="text-lg">{task.type === 'medication' ? '💊' : task.type === 'vitals' ? '❤️' : '📋'}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 truncate">{task.description}</p>
                    <p className="text-[10px] text-neutral-400 dark:text-neutral-500">{task.patientName} • {task.bed}</p>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400 rounded-lg font-bold">متأخر</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-neutral-900 dark:text-neutral-100">الأدوية القادمة</h2>
            <button onClick={() => navigate(ROUTES.MEDICATIONS)} className="text-xs text-primary-500 font-bold hover:text-primary-600">عرض الكل</button>
          </div>
          {upcomingMeds.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-3xl mb-2">💊</p>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">لا توجد أدوية مجدولة</p>
            </div>
          ) : (
            <div className="space-y-2">
              {upcomingMeds.map(med => (
                <div key={med.id} className="flex items-center gap-3 p-3 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl">
                  <span className="text-lg">💊</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 truncate">{med.name}</p>
                    <p className="text-[10px] text-neutral-400 dark:text-neutral-500">{med.patientName} • {med.bed} • {med.dosage}</p>
                  </div>
                  <span className="text-[10px] text-neutral-400">{med.scheduledTime}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {criticalPatients.length > 0 && (
        <div className="bg-warning-50 dark:bg-warning-900/10 border border-warning-200 dark:border-warning-800 rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">⚠️</span>
            <h2 className="font-bold text-warning-700 dark:text-warning-400">مرضى يحتاجون عناية خاصة</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {criticalPatients.map(p => (
              <div key={p.id} className="bg-white dark:bg-neutral-800 p-3 rounded-xl flex items-center gap-3">
                <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs', p.gender === 'أنثى' ? 'bg-pink-500' : 'bg-blue-500')}>
                  {p.name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 truncate">{p.name}</p>
                  <p className="text-[10px] text-neutral-400 dark:text-neutral-500">{p.bed} {p.fallRisk && '• خطر سقوط'} {p.isolation && '• عزل'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
