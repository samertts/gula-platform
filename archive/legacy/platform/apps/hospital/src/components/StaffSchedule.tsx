import { useState } from 'react';
import { Card, CardHeader, CardBody, Badge, useRTL } from '@gula/ui-platform';

interface Shift {
  id: string;
  staffName: string;
  staffNameAr: string;
  role: string;
  roleAr: string;
  shift: 'morning' | 'evening' | 'night' | 'on_call' | 'off';
  startTime: string;
  endTime: string;
  ward: string;
  wardAr: string;
}

const MOCK_SHIFTS: Shift[] = [
  { id: 's1', staffName: 'Dr. Ahmed Samarrai', staffNameAr: 'د. أحمد السامرائي', role: 'Consultant', roleAr: 'استشاري', shift: 'morning', startTime: '08:00', endTime: '15:00', ward: 'ER', wardAr: 'الطوارئ' },
  { id: 's2', staffName: 'Dr. Khalid Ani', staffNameAr: 'د. خالد العاني', role: 'Surgeon', roleAr: 'جراح', shift: 'morning', startTime: '08:00', endTime: '15:00', ward: 'Surgery', wardAr: 'الجراحة' },
  { id: 's3', staffName: 'Nurse Fatima Noor', staffNameAr: 'م. فاطمة نور', role: 'Head Nurse', roleAr: 'رئيسة تمريض', shift: 'morning', startTime: '07:00', endTime: '15:00', ward: 'ICU', wardAr: 'العناية المركزة' },
  { id: 's4', staffName: 'Dr. Maryam Kadhim', staffNameAr: 'د. مريم الكاظمي', role: 'Pediatrician', roleAr: 'طبيبة أطفال', shift: 'evening', startTime: '15:00', endTime: '22:00', ward: 'Pediatrics', wardAr: 'الأطفال' },
  { id: 's5', staffName: 'Nurse Hassan Ali', staffNameAr: 'م. حسن علي', role: 'Nurse', roleAr: 'ممرض', shift: 'night', startTime: '22:00', endTime: '07:00', ward: 'ER', wardAr: 'الطوارئ' },
  { id: 's6', staffName: 'Dr. Hamed Najjar', staffNameAr: 'د. حامد النجار', role: 'Cardiologist', roleAr: 'طبيب قلب', shift: 'on_call', startTime: '08:00', endTime: '08:00', ward: 'Cardiology', wardAr: 'القلب' },
];

const SHIFT_STYLES: Record<string, { bg: string; text: string; label: string; labelAr: string }> = {
  morning: { bg: 'bg-yellow-100 dark:bg-yellow-900/20', text: 'text-yellow-700 dark:text-yellow-300', label: 'Morning', labelAr: 'صباحي' },
  evening: { bg: 'bg-blue-100 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-300', label: 'Evening', labelAr: 'مسائي' },
  night: { bg: 'bg-indigo-100 dark:bg-indigo-900/20', text: 'text-indigo-700 dark:text-indigo-300', label: 'Night', labelAr: 'ليلي' },
  on_call: { bg: 'bg-purple-100 dark:bg-purple-900/20', text: 'text-purple-700 dark:text-purple-300', label: 'On Call', labelAr: 'مناوبة' },
  off: { bg: 'bg-neutral-100 dark:bg-neutral-800', text: 'text-neutral-500', label: 'Off', labelAr: 'إجازة' },
};

export function StaffSchedule() {
  const { isRtl } = useRTL();
  const [shifts] = useState(MOCK_SHIFTS);
  const today = new Date().toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });

  return (
    <Card>
      <CardHeader
        title={isRtl ? 'جدول المناوبات' : 'Staff Schedule'}
        subtitle={today}
      />
      <CardBody>
        <div className="space-y-3">
          {shifts.map(s => {
            const style = SHIFT_STYLES[s.shift];
            return (
              <div key={s.id} className={`p-3 rounded-lg ${style.bg}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                      {isRtl ? s.staffNameAr : s.staffName}
                    </p>
                    <p className="text-xs text-neutral-500">{isRtl ? s.roleAr : s.role}</p>
                  </div>
                  <Badge variant="info" size="sm">{isRtl ? s.wardAr : s.ward}</Badge>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className={`text-xs font-medium ${style.text}`}>
                    {isRtl ? style.labelAr : style.label}
                  </span>
                  <span className="text-xs text-neutral-400">
                    {s.startTime} - {s.endTime}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </CardBody>
    </Card>
  );
}
