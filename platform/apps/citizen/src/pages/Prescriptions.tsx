import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { usePrescriptions } from '../hooks/useHealthData';
import { MedicationReminder } from '../components/MedicationReminder';

export function Prescriptions() {
  const { data: prescriptions, isLoading, error } = usePrescriptions();
  const [filter, setFilter] = useState<'all' | 'active' | 'past'>('active');

  const activePerscriptions = prescriptions.filter(
    (p) => p.status === 'active' && new Date(p.expiryDate) >= new Date(),
  );
  const pastPerscriptions = prescriptions.filter(
    (p) => p.status !== 'active' || new Date(p.expiryDate) < new Date(),
  );

  const filtered = filter === 'active' ? activePerscriptions : filter === 'past' ? pastPerscriptions : prescriptions;

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
      <div className="flex items-center gap-2 mb-6">
        {(['active', 'past', 'all'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              'px-4 py-2 rounded-xl text-xs font-bold transition-all',
              filter === f
                ? 'bg-primary-500 text-white shadow-lg shadow-primary-200 dark:shadow-primary-900/30'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400',
            )}
          >
            {f === 'active' ? 'النشطة' : f === 'past' ? 'السابقة' : 'الكل'}
          </button>
        ))}
        <div className="flex-1" />
        <span className="text-xs text-neutral-400">{activePerscriptions.length} نشطة</span>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">
            {filter === 'active' ? 'لا توجد أدوية نشطة' : 'لا توجد وصفات طبية'}
          </p>
          <p className="text-[10px] text-neutral-400">سيتم عرض الأدوية والوصفات الطبية هنا</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((prescription) => (
            <MedicationReminder key={prescription.id} prescription={prescription} />
          ))}
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
