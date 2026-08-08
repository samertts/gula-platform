import { cn } from '@gula/ui-platform';
import type { Consent, ConsentPermission } from '../types';

interface ConsentToggleProps {
  consent: Consent;
  onRevoke?: (id: string) => void;
  onExtend?: (id: string) => void;
  className?: string;
}

const scopeLabels: Record<string, string> = {
  full: 'كامل',
  limited: 'محدود',
  emergency: 'طوارئ',
};

const scopeColors: Record<string, string> = {
  full: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  limited: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
  emergency: 'bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400',
};

const permissionLabels: Record<ConsentPermission, string> = {
  read_vitals: 'قراءة العلامات الحيوية',
  read_labs: 'قراءة نتائج المختبر',
  read_history: 'قراءة التاريخ الطبي',
  read_imaging: 'قراءة تقارير الأشعة',
  read_prescriptions: 'قراءة الوصفات الطبية',
  write_order: 'كتابة الأوامر الطبية',
  emergency_access: 'وصول طارئ',
};

export function ConsentToggle({ consent, onRevoke, onExtend, className }: ConsentToggleProps) {
  const isActive = consent.status === 'active';
  const isExpired = consent.status === 'expired';
  const expiresSoon = consent.expiresAt && new Date(consent.expiresAt) < new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

  return (
    <div className={cn(
      'bg-white dark:bg-neutral-800 rounded-2xl p-5 border',
      isActive
        ? 'border-neutral-200 dark:border-neutral-700'
        : 'border-neutral-100 dark:border-neutral-700/50 bg-neutral-50 dark:bg-neutral-800/50',
      className,
    )}>
      <div className="flex items-start justify-between mb-4">
        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-neutral-900 dark:text-neutral-50 truncate">
            {consent.providerName}
          </h3>
          <p className="text-[10px] text-neutral-500 mt-0.5">
            {consent.providerType === 'lab' ? 'مختبر' :
             consent.providerType === 'hospital' ? 'مستشفى' :
             consent.providerType === 'clinic' ? 'عيادة' :
             consent.providerType === 'pharmacy' ? 'صيدلية' : 'بحث علمي'}
          </p>
        </div>
        <span className={cn('px-2 py-0.5 rounded-lg text-[10px] font-bold', scopeColors[consent.scope])}>
          {scopeLabels[consent.scope]}
        </span>
      </div>

      <div className="space-y-2 mb-4">
        {consent.permissions.map((permission) => (
          <div key={permission} className="flex items-center gap-2">
            <svg className="w-4 h-4 text-success-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-xs text-neutral-700 dark:text-neutral-300">
              {permissionLabels[permission]}
            </span>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between text-[10px] text-neutral-400 mb-4">
        <span>منذ {new Date(consent.grantedAt).toLocaleDateString('ar-IQ')}</span>
        {consent.expiresAt && (
          <span className={cn(
            expiresSoon && isActive && 'text-warning-600 font-bold',
          )}>
            {isExpired ? 'منتهي' : `ينتهي ${new Date(consent.expiresAt).toLocaleDateString('ar-IQ')}`}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {isActive && onRevoke && (
          <button
            onClick={() => onRevoke(consent.id)}
            className="flex-1 px-4 py-2 border border-danger-200 dark:border-danger-700 text-danger-600 dark:text-danger-400 rounded-xl text-xs font-bold hover:bg-danger-50 dark:hover:bg-danger-900/20 transition-colors"
          >
            سحب الموافقة
          </button>
        )}
        {expiresSoon && isActive && onExtend && (
          <button
            onClick={() => onExtend(consent.id)}
            className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-xl text-xs font-bold hover:bg-primary-600 transition-colors"
          >
            تمديد
          </button>
        )}
      </div>
    </div>
  );
}
