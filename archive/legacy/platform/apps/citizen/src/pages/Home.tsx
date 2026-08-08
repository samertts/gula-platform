import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { useOffline } from '../contexts/OfflineContext';
import { useHealthScore } from '../hooks/useHealthData';
import { ROUTES } from '../utils/routes';

const quickActions = [
  { path: ROUTES.HEALTH_ID, label: 'بطاقتي الصحية', icon: 'card', color: 'bg-primary-500' },
  { path: ROUTES.LAB_RESULTS, label: 'نتائج المختبر', icon: 'lab', color: 'bg-indigo-500' },
  { path: ROUTES.APPOINTMENTS, label: 'المواعيد', icon: 'calendar', color: 'bg-emerald-500' },
  { path: ROUTES.PRESCRIPTIONS, label: 'الأدوية', icon: 'med', color: 'bg-amber-500' },
  { path: ROUTES.FAMILY, label: 'العائلة', icon: 'family', color: 'bg-rose-500' },
  { path: ROUTES.HEALTH_ASSISTANT, label: 'المساعد الصحي', icon: 'ai', color: 'bg-violet-500' },
];

const actionIcons: Record<string, React.ReactNode> = {
  card: <path key="card" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />,
  lab: <path key="lab" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />,
  calendar: <path key="calendar" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />,
  med: <path key="med" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />,
  family: <path key="family" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />,
  ai: <path key="ai" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />,
};

export function Home() {
  const { user } = useAuth();
  const { isOffline } = useOffline();
  const { data: healthScore, isLoading: scoreLoading } = useHealthScore();
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting('صباح الخير');
    else if (hour < 18) setGreeting('مساء الخير');
    else setGreeting('مساء الخير');
  }, []);

  if (!user) return null;

  return (
    <div className="pb-24">
      <div className="px-4 pt-6 pb-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-0.5">{greeting}</p>
            <h2 className="text-xl font-black text-neutral-900 dark:text-neutral-50">{user.name}</h2>
          </div>
          {!isOffline && healthScore && (
            <div className="text-center">
              <div className={cn(
                'w-16 h-16 rounded-2xl flex items-center justify-center font-black text-lg',
                healthScore.overall >= 80 ? 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400' :
                healthScore.overall >= 60 ? 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400' :
                'bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400',
              )}>
                {healthScore.overall}
              </div>
              <p className="text-[9px] font-bold text-neutral-400 mt-1">الدرجة الصحية</p>
            </div>
          )}
        </div>

        <Link
          to={ROUTES.HEALTH_ID}
          className="block bg-gradient-to-br from-primary-600 to-primary-900 text-white rounded-3xl p-6 shadow-xl mb-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/70 mb-1">الهوية الصحية</p>
              <p className="text-lg font-black">{user.name}</p>
              <p className="text-sm font-bold text-white/80 mt-1">{user.nationalId.replace(/(\d{3})(\d{3})(\d{4})(\d{4})/, '$1-$2-$3-$4')}</p>
            </div>
            <svg className="w-12 h-12 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
            </svg>
          </div>
        </Link>

        <div className="grid grid-cols-3 gap-3">
          {quickActions.map((action) => (
            <Link
              key={action.path}
              to={action.path}
              className="flex flex-col items-center gap-2 p-4 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 shadow-sm hover:shadow-md hover:border-primary-200 dark:hover:border-primary-700 transition-all"
            >
              <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', action.color)}>
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {actionIcons[action.icon]}
                </svg>
              </div>
              <span className="text-[10px] font-bold text-neutral-600 dark:text-neutral-400 text-center leading-tight">
                {action.label}
              </span>
            </Link>
          ))}
        </div>
      </div>

      <div className="px-4 mt-6">
        <h3 className="text-sm font-black text-neutral-900 dark:text-neutral-50 mb-3">
          نشاطات سريعة
        </h3>
        <div className="space-y-3">
          <Link
            to={ROUTES.APPOINTMENTS}
            className="flex items-center gap-4 p-4 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 shadow-sm"
          >
            <div className="w-12 h-12 rounded-xl bg-primary-50 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="3" y="4" width="18" height="18" rx="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 2v4M8 2v4M3 10h18" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-bold text-neutral-900 dark:text-neutral-50">حجز موعد جديد</p>
              <p className="text-[10px] text-neutral-500">استشارة طبية أو فحص دوري</p>
            </div>
            <svg className="w-5 h-5 text-neutral-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>

          <Link
            to={ROUTES.HEALTH_ASSISTANT}
            className="flex items-center gap-4 p-4 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 shadow-sm"
          >
            <div className="w-12 h-12 rounded-xl bg-violet-50 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 dark:text-violet-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-bold text-neutral-900 dark:text-neutral-50">المساعد الصحي الذكي</p>
              <p className="text-[10px] text-neutral-500">اسأل عن الأعراض والتوصيات</p>
            </div>
            <svg className="w-5 h-5 text-neutral-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>

      {isOffline && (
        <div className="px-4 mt-6">
          <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-2xl">
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <p className="text-xs font-bold text-amber-700 dark:text-amber-400">وضع غير متصل</p>
            </div>
            <p className="text-[11px] text-amber-600 dark:text-amber-500">
              يتم عرض البيانات المخزنة مؤقتاً. سيتم المزامنة تلقائياً عند الاتصال.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
