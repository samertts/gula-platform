import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import type { FiveRights, Medication } from '@/utils/types';

interface MedicationVerificationProps {
  medication: Medication;
  onVerify: (rights: FiveRights) => void;
  onCancel: () => void;
  loading?: boolean;
}

const RIGHTS: { key: keyof FiveRights; label: string; icon: string }[] = [
  { key: 'rightPatient', label: 'المريض الصحيح', icon: '👤' },
  { key: 'rightMedication', label: 'الدواء الصحيح', icon: '💊' },
  { key: 'rightDose', label: 'الجرعة الصحيحة', icon: '⚖️' },
  { key: 'rightRoute', label: 'الطريق الصحيح', icon: '💉' },
  { key: 'rightTime', label: 'الوقت الصحيح', icon: '⏰' },
];

export function MedicationVerification({ medication, onVerify, onCancel, loading }: MedicationVerificationProps) {
  const [rights, setRights] = useState<FiveRights>({
    rightPatient: false,
    rightMedication: false,
    rightDose: false,
    rightRoute: false,
    rightTime: false,
  });
  const [currentStep, setCurrentStep] = useState(0);

  const allVerified = Object.values(rights).every(Boolean);

  const toggleRight = (key: keyof FiveRights) => {
    setRights(prev => ({ ...prev, [key]: !prev[key] }));
    if (currentStep < RIGHTS.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-primary-50 dark:bg-primary-900/20 p-4 rounded-2xl border border-primary-200 dark:border-primary-800">
        <h3 className="font-bold text-primary-700 dark:text-primary-300 mb-2">التحقق من الحقوق الخمسة</h3>
        <p className="text-sm text-primary-600 dark:text-primary-400">{medication.name} - {medication.dosage}</p>
        <p className="text-xs text-primary-500 dark:text-primary-400 mt-1">
          المريض: {medication.patientName} • السرير: {medication.bed}
        </p>
      </div>

      <div className="flex gap-1.5">
        {RIGHTS.map((r, i) => (
          <div
            key={r.key}
            className={cn(
              'flex-1 h-2 rounded-full transition-colors',
              rights[r.key] ? 'bg-success-500' : i === currentStep ? 'bg-primary-500' : 'bg-neutral-200 dark:bg-neutral-600',
            )}
          />
        ))}
      </div>

      <div className="space-y-3">
        {RIGHTS.map((r, i) => (
          <button
            key={r.key}
            type="button"
            disabled={i > currentStep}
            onClick={() => toggleRight(r.key)}
            className={cn(
              'w-full text-right p-4 rounded-2xl border-2 transition-all duration-200 flex items-center gap-3',
              rights[r.key]
                ? 'border-success-500 bg-success-50 dark:bg-success-900/20'
                : i === currentStep
                  ? 'border-primary-500 bg-white dark:bg-neutral-800 shadow-md'
                  : 'border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50 opacity-50',
            )}
          >
            <span className="text-2xl">{r.icon}</span>
            <div className="flex-1 min-w-0">
              <p className={cn(
                'font-bold text-sm',
                rights[r.key]
                  ? 'text-success-700 dark:text-success-400'
                  : 'text-neutral-700 dark:text-neutral-300',
              )}>
                {r.label}
              </p>
              {i === currentStep && !rights[r.key] && (
                <p className="text-xs text-primary-500 mt-0.5">اضغط للتحقق</p>
              )}
              {rights[r.key] && (
                <p className="text-xs text-success-500 mt-0.5">✓ تم التحقق</p>
              )}
            </div>
            {rights[r.key] && (
              <svg className="w-5 h-5 text-success-500 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            )}
          </button>
        ))}
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-3 px-4 bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-2xl font-bold text-sm hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors"
        >
          إلغاء
        </button>
        <button
          type="button"
          disabled={!allVerified || loading}
          onClick={() => onVerify(rights)}
          className={cn(
            'flex-1 py-3 px-4 bg-success-500 text-white rounded-2xl font-bold text-sm transition-colors',
            'hover:bg-success-600 active:bg-success-700',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              جاري التحقق...
            </span>
          ) : (
            'تأكيد الإعطاء'
          )}
        </button>
      </div>
    </div>
  );
}
