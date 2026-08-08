import { useState } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { useAppointments } from '../hooks/useAppointments';
import { AppointmentCard } from '../components/AppointmentCard';

export function Appointments() {
  const { appointments, upcomingAppointments, pastAppointments, isLoading, error, refetch, cancelAppointment, bookAppointment } = useAppointments();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'past'>('upcoming');

  const displayAppointments = filter === 'upcoming' ? upcomingAppointments : filter === 'past' ? pastAppointments : appointments;

  async function handleCancel(id: string) {
    try {
      await cancelAppointment(id);
    } catch {}
  }

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-40 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="flex items-center gap-2 mb-6">
        {(['upcoming', 'past', 'all'] as const).map((f) => (
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
            {f === 'upcoming' ? 'القادمة' : f === 'past' ? 'السابقة' : 'الكل'}
          </button>
        ))}
        <div className="flex-1" />
        <span className="text-xs text-neutral-400">{upcomingAppointments.length} موعد</span>
      </div>

      {displayAppointments.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect x="3" y="4" width="18" height="18" rx="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 2v4M8 2v4M3 10h18" />
          </svg>
          <p className="text-sm text-neutral-500 mb-4">
            {filter === 'upcoming' ? 'لا توجد مواعيد قادمة' : 'لا توجد مواعيد سابقة'}
          </p>
          <Button variant="primary" onClick={() => setShowForm(true)}>
            حجز موعد جديد
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {displayAppointments.map((appointment) => (
            <AppointmentCard
              key={appointment.id}
              appointment={appointment}
              onCancel={handleCancel}
              onJoin={(url) => window.open(url, '_blank')}
            />
          ))}
        </div>
      )}

      {displayAppointments.length > 0 && (
        <div className="mt-6">
          <Button fullWidth size="lg" onClick={() => setShowForm(true)}>
            حجز موعد جديد
          </Button>
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
