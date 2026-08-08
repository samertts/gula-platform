import { cn } from '@gula/ui-platform';
import type { EmergencyInfo as EmergencyInfoType } from '../types';

interface EmergencyInfoProps {
  info: EmergencyInfoType;
  className?: string;
}

export function EmergencyInfo({ info, className }: EmergencyInfoProps) {
  return (
    <div className={cn('bg-white dark:bg-neutral-800 rounded-3xl border-2 border-danger-200 dark:border-danger-800 overflow-hidden', className)}>
      <div className="bg-danger-500 text-white px-5 py-3 flex items-center gap-3">
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
        </svg>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/70">معلومات الطوارئ</p>
          <p className="text-sm font-black">Emergency Information</p>
        </div>
      </div>

      <div className="p-5 space-y-5">
        <div>
          <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-1">فصيلة الدم</p>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-danger-50 dark:bg-danger-900/20 text-danger-700 dark:text-danger-400 rounded-2xl font-black text-lg">
            {info.bloodType || 'غير محدد'}
          </div>
        </div>

        {info.allergies.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">الحساسية</p>
            <div className="flex flex-wrap gap-2">
              {info.allergies.map((allergy, i) => (
                <span key={i} className="px-3 py-1 bg-warning-50 dark:bg-warning-900/20 text-warning-700 dark:text-warning-400 rounded-xl text-xs font-bold">
                  {allergy}
                </span>
              ))}
            </div>
          </div>
        )}

        {info.chronicConditions.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">الحالات المزمنة</p>
            <div className="flex flex-wrap gap-2">
              {info.chronicConditions.map((condition, i) => (
                <span key={i} className="px-3 py-1 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-xl text-xs font-bold">
                  {condition}
                </span>
              ))}
            </div>
          </div>
        )}

        {info.medications.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">الأدوية الحالية</p>
            <ul className="space-y-1">
              {info.medications.map((med, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                  <svg className="w-3 h-3 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  {med}
                </li>
              ))}
            </ul>
          </div>
        )}

        {info.emergencyContacts.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">جهات الاتصال للطوارئ</p>
            <div className="space-y-2">
              {info.emergencyContacts.map((contact) => (
                <div key={contact.id} className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl">
                  <div>
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50">{contact.name}</p>
                    <p className="text-[10px] text-neutral-500">{contact.relationship}</p>
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50" dir="ltr">{contact.phone}</p>
                    {contact.isPrimary && (
                      <span className="text-[9px] font-bold text-primary-500">رئيسي</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center gap-3 pt-3 border-t border-neutral-100 dark:border-neutral-700">
          <div className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={info.organDonor}
              readOnly
              className="w-4 h-4 rounded border-neutral-300 text-primary-500"
            />
            <span className="text-xs text-neutral-600 dark:text-neutral-400">متبرع بالأعضاء</span>
          </div>
          {info.preferredHospital && (
            <span className="text-xs text-neutral-500">
              المستشفى المفضل: {info.preferredHospital}
            </span>
          )}
        </div>

        {info.notes && (
          <p className="text-xs text-neutral-500 italic bg-neutral-50 dark:bg-neutral-700/50 p-3 rounded-xl">
            {info.notes}
          </p>
        )}
      </div>
    </div>
  );
}
