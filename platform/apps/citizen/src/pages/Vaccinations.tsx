import { cn } from '@gula/ui-platform';
import { useVaccinations } from '../hooks/useHealthData';
import { VaccineRecord } from '../components/VaccineRecord';

export function Vaccinations() {
  const { data: vaccinations, isLoading, error } = useVaccinations();

  const completed = vaccinations.filter((v) => v.status === 'completed');
  const scheduled = vaccinations.filter((v) => v.status === 'scheduled');
  const overdue = vaccinations.filter((v) => v.status === 'overdue');

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-24 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      {overdue.length > 0 && (
        <div className="mb-4 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-2xl">
          <p className="text-xs font-bold text-danger-600 dark:text-danger-400 mb-1">
            تطعيمات متأخرة ({overdue.length})
          </p>
          <p className="text-[10px] text-danger-500">
            هناك تطعيمات مستحقة. يرجى تحديد موعد في أقرب وقت.
          </p>
        </div>
      )}

      {scheduled.length > 0 && (
        <div className="mb-4 p-4 bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-2xl">
          <p className="text-xs font-bold text-primary-600 dark:text-primary-400 mb-1">
            تطعيمات قادمة ({scheduled.length})
          </p>
          <p className="text-[10px] text-primary-500">لديك تطعيمات مجدولة.</p>
        </div>
      )}

      {vaccinations.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">لا توجد سجلات تطعيم</p>
          <p className="text-[10px] text-neutral-400">سيتم عرض سجلات التطعيم هنا عند توفرها</p>
        </div>
      ) : (
        <div className="space-y-6">
          {scheduled.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">المجدولة</h3>
              <div className="bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 space-y-5">
                {scheduled.map((v) => (
                  <VaccineRecord key={v.id} vaccination={v} />
                ))}
              </div>
            </div>
          )}
          {overdue.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">المتأخرة</h3>
              <div className="bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-danger-200 dark:border-danger-800 space-y-5">
                {overdue.map((v) => (
                  <VaccineRecord key={v.id} vaccination={v} />
                ))}
              </div>
            </div>
          )}
          {completed.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">المكتملة</h3>
              <div className="bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 space-y-5">
                {completed.map((v) => (
                  <VaccineRecord key={v.id} vaccination={v} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400">{error}</p>
        </div>
      )}
    </div>
  );
}
