import { cn } from '@gula/ui-platform';
import type { Appointment } from '../types';

interface AppointmentCardProps {
  appointment: Appointment;
  onCancel?: (id: string) => void;
  onJoin?: (url: string) => void;
  className?: string;
}

const typeLabels: Record<string, string> = {
  checkup: 'فحص دوري',
  consultation: 'استشارة',
  followup: 'متابعة',
  emergency: 'طوارئ',
  lab_test: 'تحليل',
  vaccination: 'تطعيم',
};

const statusColors: Record<string, string> = {
  scheduled: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  confirmed: 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400',
  in_progress: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
  completed: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  cancelled: 'bg-danger-100 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400',
  no_show: 'bg-danger-100 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400',
};

const statusLabels: Record<string, string> = {
  scheduled: 'مجدول',
  confirmed: 'مؤكد',
  in_progress: 'قيد التنفيذ',
  completed: 'مكتمل',
  cancelled: 'ملغي',
  no_show: 'لم يحضر',
};

export function AppointmentCard({ appointment, onCancel, onJoin, className }: AppointmentCardProps) {
  const appointmentDate = new Date(appointment.date);
  const isUpcoming = appointment.status === 'scheduled' || appointment.status === 'confirmed';

  return (
    <div className={cn('bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 shadow-sm', className)}>
      <div className="flex items-start justify-between mb-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('px-2 py-0.5 rounded-lg text-[10px] font-bold', statusColors[appointment.status])}>
              {statusLabels[appointment.status]}
            </span>
            {appointment.isVirtual && (
              <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-lg text-[10px] font-bold">
                عن بعد
              </span>
            )}
          </div>
          <h3 className="font-black text-neutral-900 dark:text-neutral-50 truncate">
            {appointment.providerName}
          </h3>
          {appointment.providerSpecialty && (
            <p className="text-xs text-neutral-500 mt-0.5">{appointment.providerSpecialty}</p>
          )}
        </div>
        <div className="text-left shrink-0">
          <p className="text-lg font-black text-neutral-900 dark:text-neutral-50 leading-none">
            {appointmentDate.toLocaleDateString('ar-IQ', { day: 'numeric' })}
          </p>
          <p className="text-[10px] font-bold text-neutral-400">
            {appointmentDate.toLocaleDateString('ar-IQ', { month: 'short' })}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400 mb-4">
        <div className="flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6l4 2" />
          </svg>
          <span className="text-xs font-bold">{appointment.startTime} - {appointment.endTime}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="text-xs font-bold truncate">{appointment.facilityName}</span>
        </div>
      </div>

      <p className="text-xs text-neutral-500 mb-4">
        {typeLabels[appointment.type] || appointment.type}
      </p>

      {appointment.notes && (
        <p className="text-xs text-neutral-500 mb-4 italic bg-neutral-50 dark:bg-neutral-700/50 p-3 rounded-xl">
          {appointment.notes}
        </p>
      )}

      {isUpcoming && (
        <div className="flex items-center gap-2 pt-3 border-t border-neutral-100 dark:border-neutral-700">
          {appointment.isVirtual && appointment.meetingUrl && onJoin && (
            <button
              onClick={() => onJoin(appointment.meetingUrl!)}
              className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-xl text-xs font-bold hover:bg-primary-600 transition-colors"
            >
              انضم إلى الجلسة
            </button>
          )}
          {onCancel && (
            <button
              onClick={() => onCancel(appointment.id)}
              className="px-4 py-2 border border-neutral-200 dark:border-neutral-600 text-neutral-600 dark:text-neutral-400 rounded-xl text-xs font-bold hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
            >
              إلغاء
            </button>
          )}
        </div>
      )}
    </div>
  );
}
