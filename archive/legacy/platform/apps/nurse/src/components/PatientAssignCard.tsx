import { cn } from '@gula/ui-platform';
import type { Patient } from '@/utils/types';

interface PatientAssignCardProps {
  patient: Patient;
  onClick?: () => void;
  active?: boolean;
}

const isolationColors: Record<string, string> = {
  contact: 'bg-yellow-500',
  airborne: 'bg-red-500',
  droplet: 'bg-blue-500',
  protective: 'bg-purple-500',
};

export function PatientAssignCard({ patient, onClick, active }: PatientAssignCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-right p-4 rounded-2xl border-2 transition-all duration-200',
        'hover:shadow-md hover:-translate-y-0.5',
        active
          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-md'
          : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800',
      )}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className={cn(
            'w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm shrink-0',
            patient.gender === 'أنثى' ? 'bg-pink-500' : 'bg-blue-500',
          )}>
            {patient.name.charAt(0)}
          </div>
          <div className="min-w-0">
            <p className="font-bold text-neutral-900 dark:text-neutral-100 truncate">{patient.name}</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
              {patient.age} سنة • {patient.gender} • {patient.mrn}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {patient.isolation && (
            <span className={cn('w-2.5 h-2.5 rounded-full', isolationColors[patient.isolation] || 'bg-neutral-400')}
              title={`عزل ${patient.isolation}`} />
          )}
          {patient.fallRisk && (
            <span className="text-xs px-1.5 py-0.5 bg-warning-100 dark:bg-warning-900/30 text-warning-600 dark:text-warning-400 font-bold rounded">
              سقوط
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-neutral-50 dark:bg-neutral-700/50 p-2 rounded-xl">
          <span className="text-neutral-400 dark:text-neutral-500">السرير</span>
          <p className="font-bold text-neutral-700 dark:text-neutral-300">{patient.bed}</p>
        </div>
        <div className="bg-neutral-50 dark:bg-neutral-700/50 p-2 rounded-xl">
          <span className="text-neutral-400 dark:text-neutral-500">التشخيص</span>
          <p className="font-bold text-neutral-700 dark:text-neutral-300 truncate">{patient.diagnosis}</p>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-neutral-100 dark:border-neutral-700 flex items-center justify-between text-xs">
        <span className="text-neutral-400 dark:text-neutral-500">
          د. {patient.attendingPhysician}
        </span>
        <span className="text-neutral-400 dark:text-neutral-500">
          {new Date(patient.admissionDate).toLocaleDateString('ar-IQ')}
        </span>
      </div>
    </button>
  );
}
