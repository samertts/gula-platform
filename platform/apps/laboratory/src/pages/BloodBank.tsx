import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function BloodBank() {
  const [samples] = useState([
    { id: 'BB-001', sampleId: 'SMP-8901', patient: 'Ali Mohammed', bloodGroup: 'A+', rhType: 'positive' as const, crossmatch: 'compatible', status: 'final' },
    { id: 'BB-002', sampleId: 'SMP-8905', patient: 'Fatima Hassan', bloodGroup: 'O-', rhType: 'negative' as const, crossmatch: 'pending', status: 'pending' },
    { id: 'BB-003', sampleId: 'SMP-8910', patient: 'Hussein Ali', bloodGroup: 'B+', rhType: 'positive' as const, antibodyScreen: 'negative', status: 'final' },
  ]);

  const [inventory] = useState([
    { type: 'دم كامل', units: 24, status: 'adequate' as const },
    { type: 'RBCs مركزة', units: 15, status: 'adequate' as const },
    { type: 'صفائح دموية', units: 5, status: 'low' as const },
    { type: 'بلازما طازجة مجمدة', units: 8, status: 'adequate' as const },
    { type: 'راسب قري', units: 3, status: 'critical' as const },
  ]);

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">بنك الدم</h1>
      <p className="text-sm text-neutral-500 -mt-5">إدارة فصائل الدم والتوافق والمخزون</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {inventory.map(item => (
          <div key={item.type} className={cn(
            'p-5 rounded-2xl border-2 bg-white dark:bg-neutral-800',
            item.status === 'critical' ? 'border-danger-300 dark:border-danger-700' :
            item.status === 'low' ? 'border-warning-300 dark:border-warning-700' :
            'border-success-200 dark:border-success-700',
          )}>
            <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{item.type}</p>
            <p className={cn(
              'text-2xl font-black my-2',
              item.status === 'critical' ? 'text-danger-500' :
              item.status === 'low' ? 'text-warning-500' :
              'text-success-500',
            )}>{item.units}</p>
            <span className={cn(
              'text-[10px] font-black px-2 py-0.5 rounded-full',
              item.status === 'critical' ? 'bg-danger-50 text-danger-600' :
              item.status === 'low' ? 'bg-warning-50 text-warning-600' :
              'bg-success-50 text-success-600',
            )}>
              {item.status === 'critical' ? 'حرج' : item.status === 'low' ? 'منخفض' : 'كاف'}
            </span>
          </div>
        ))}
      </div>

      <Card>
        <CardHeader><span className="font-bold">عينات بنك الدم</span></CardHeader>
        <CardBody>
          <div className="space-y-3">
            {samples.map(s => (
              <div key={s.id} className="flex items-center justify-between p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-danger-100 dark:bg-danger-900/30 flex items-center justify-center text-danger-600 dark:text-danger-400 font-black text-lg">
                    {s.bloodGroup}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{s.patient}</p>
                    <p className="text-xs text-neutral-500">{s.sampleId} • فصيلة {s.bloodGroup} • {s.rhType === 'positive' ? 'موجب' : 'سالب'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'px-2 py-0.5 rounded text-[9px] font-bold',
                    s.status === 'final' ? 'bg-success-50 text-success-600' : 'bg-warning-50 text-warning-600',
                  )}>
                    {s.status === 'final' ? 'مكتمل' : 'معلق'}
                  </span>
                  <button type="button" className="px-3 py-1.5 text-xs font-bold text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-xl">تفاصيل</button>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
