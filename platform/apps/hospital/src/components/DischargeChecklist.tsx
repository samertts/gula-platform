import { useState } from 'react';
import { Button, useRTL } from '@gula/ui-platform';

interface DischargeChecklistProps {
  patient: {
    id: string;
    patientName: string;
    patientNameAr: string;
    diagnosis: string;
    diagnosisAr: string;
    doctor: string;
    doctorAr: string;
    lengthOfStay: number;
    bedNumber: string;
  };
  onComplete: () => void;
}

const CHECKLIST_ITEMS = [
  { id: 'medication', keyAr: 'مراجعة الأدوية', keyEn: 'Medication Reconciliation' },
  { id: 'summary', keyAr: 'ملخص التخريج', keyEn: 'Discharge Summary' },
  { id: 'instructions', keyAr: 'تعليمات التخريج', keyEn: 'Discharge Instructions' },
  { id: 'followup', keyAr: 'موعد المتابعة', keyEn: 'Follow-up Appointment' },
  { id: 'prescriptions', keyAr: 'الوصفات الطبية', keyEn: 'Prescriptions' },
  { id: 'certificate', keyAr: 'شهادة التخريج', keyEn: 'Discharge Certificate' },
  { id: 'billing', keyAr: 'التسوية المالية', keyEn: 'Billing Clearance' },
  { id: 'belongings', keyAr: 'تسليم الأغراض الشخصية', keyEn: 'Personal Belongings' },
  { id: 'transport', keyAr: 'ترتيبات النقل', keyEn: 'Transport Arrangements' },
  { id: 'nursing', keyAr: 'تقرير التمريض', keyEn: 'Nursing Handover' },
];

export function DischargeChecklist({ patient, onComplete }: DischargeChecklistProps) {
  const { isRtl } = useRTL();
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [dischargeNotes, setDischargeNotes] = useState('');

  const toggleItem = (id: string) => {
    setChecked(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const progress = Math.round((checked.size / CHECKLIST_ITEMS.length) * 100);

  return (
    <div className="space-y-6">
      <div className="bg-neutral-50 dark:bg-neutral-800/50 rounded-lg p-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-xs text-neutral-400">{isRtl ? 'المريض' : 'Patient'}</p>
            <p className="font-medium text-neutral-900 dark:text-neutral-50">
              {isRtl ? patient.patientNameAr : patient.patientName}
            </p>
          </div>
          <div>
            <p className="text-xs text-neutral-400">{isRtl ? 'التشخيص' : 'Diagnosis'}</p>
            <p className="font-medium text-neutral-900 dark:text-neutral-50">
              {isRtl ? patient.diagnosisAr : patient.diagnosis}
            </p>
          </div>
          <div>
            <p className="text-xs text-neutral-400">{isRtl ? 'الطبيب المعالج' : 'Doctor'}</p>
            <p className="font-medium text-neutral-900 dark:text-neutral-50">{isRtl ? patient.doctorAr : patient.doctor}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-400">{isRtl ? 'مدة الإقامة' : 'Length of Stay'}</p>
            <p className="font-medium text-neutral-900 dark:text-neutral-50">{patient.lengthOfStay} {isRtl ? 'أيام' : 'days'}</p>
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-bold text-neutral-700 dark:text-neutral-300">
            {isRtl ? 'قائمة التخريج' : 'Discharge Checklist'}
          </h3>
          <span className="text-xs font-medium text-primary-600 dark:text-primary-400">{progress}%</span>
        </div>
        <div className="h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden mb-4">
          <div className="h-full bg-primary-500 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>

        <div className="space-y-1">
          {CHECKLIST_ITEMS.map(item => (
            <label
              key={item.id}
              className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                checked.has(item.id)
                  ? 'bg-primary-50 dark:bg-primary-900/10'
                  : 'hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
              }`}
            >
              <input
                type="checkbox"
                checked={checked.has(item.id)}
                onChange={() => toggleItem(item.id)}
                className="w-4 h-4 rounded border-neutral-300 dark:border-neutral-600 text-primary-600 focus:ring-primary-500"
              />
              <span className={`text-sm flex-1 ${
                checked.has(item.id)
                  ? 'line-through text-neutral-400'
                  : 'text-neutral-700 dark:text-neutral-300'
              }`}>
                {isRtl ? item.keyAr : item.keyEn}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
          {isRtl ? 'ملاحظات التخريج' : 'Discharge Notes'}
        </label>
        <textarea
          value={dischargeNotes}
          onChange={e => setDischargeNotes(e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-sm text-neutral-900 dark:text-neutral-50 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder={isRtl ? 'أي ملاحظات إضافية...' : 'Any additional notes...'}
        />
      </div>

      <div className="flex items-center justify-end gap-3 pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <Button type="button" variant="outline" onClick={onComplete}>
          {isRtl ? 'إلغاء' : 'Cancel'}
        </Button>
        <Button
          type="button"
          disabled={checked.size < CHECKLIST_ITEMS.length}
          onClick={() => {
            onComplete();
          }}
        >
          {isRtl ? 'إتمام التخريج' : 'Complete Discharge'}
        </Button>
      </div>
    </div>
  );
}
