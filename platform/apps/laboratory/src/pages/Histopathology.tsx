import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function Histopathology() {
  const [cases] = useState([
    { id: 'HP-001', sampleId: 'SMP-9001', patient: 'Mariam Ibrahim', specimenType: 'نسيج كبد', stains: ['H&E', 'Masson'], diagnosis: 'تليف كبدي', status: 'final', pathologist: 'د. أحمد' },
    { id: 'HP-002', sampleId: 'SMP-9010', patient: 'Youssef Naji', specimenType: 'نسيج جلد', stains: ['H&E', 'IHC'], diagnosis: 'معلق', status: 'pending', pathologist: 'د. سارة' },
    { id: 'HP-003', sampleId: 'SMP-9022', patient: 'Aisha Khalid', specimenType: 'عقدة لمفاوية', stains: ['H&E'], diagnosis: 'تضخم حميد', status: 'preliminary', pathologist: 'د. أحمد' },
  ]);

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">الأنسجة المرضية</h1>
      <p className="text-sm text-neutral-500 -mt-5">إدارة حالات علم الأنسجة المرضية</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {cases.map(c => (
          <Card key={c.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-neutral-500">{c.sampleId}</span>
                <span className={cn(
                  'px-2 py-0.5 rounded text-[9px] font-bold',
                  c.status === 'final' ? 'bg-success-50 text-success-600' :
                  c.status === 'preliminary' ? 'bg-warning-50 text-warning-600' :
                  'bg-neutral-100 text-neutral-500',
                )}>
                  {c.status === 'final' ? 'نهائي' : c.status === 'preliminary' ? 'أولي' : 'معلق'}
                </span>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{c.patient}</p>
              <p className="text-xs text-neutral-500">نوع العينة: {c.specimenType}</p>
              <div className="flex flex-wrap gap-1">
                {c.stains.map(stain => (
                  <span key={stain} className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded text-[9px] font-medium">{stain}</span>
                ))}
              </div>
              <p className={cn(
                'text-sm font-bold',
                c.diagnosis === 'معلق' ? 'text-neutral-400' : 'text-neutral-900 dark:text-neutral-100',
              )}>
                {c.diagnosis}
              </p>
              <p className="text-xs text-neutral-500">أخصائي: {c.pathologist}</p>
              <div className="flex gap-2 pt-2">
                <button type="button" className="flex-1 py-2 bg-primary-500 text-white rounded-xl text-xs font-bold hover:bg-primary-600">تقرير</button>
                <button type="button" className="px-3 py-2 bg-neutral-100 dark:bg-neutral-700 rounded-xl text-xs font-bold">صور</button>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
}
