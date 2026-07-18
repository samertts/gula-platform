import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function Microbiology() {
  const [cultures] = useState([
    { id: 'MC-001', sampleId: 'SMP-8832', patient: 'Ahmed Mohammed', organism: 'E. coli', growth: 'heavy', status: 'final', date: '2026-07-15' },
    { id: 'MC-002', sampleId: 'SMP-8835', patient: 'Sarah Ali', organism: 'S. aureus', growth: 'moderate', status: 'preliminary', date: '2026-07-16' },
    { id: 'MC-003', sampleId: 'SMP-8840', patient: 'Khalid Omar', organism: 'Pending', growth: 'none', status: 'pending', date: '2026-07-16' },
  ]);

  const antibiotics = [
    { name: 'Amoxicillin', sensitive: true },
    { name: 'Ciprofloxacin', sensitive: true },
    { name: 'Ceftriaxone', sensitive: false },
    { name: 'Gentamicin', sensitive: true },
    { name: 'Vancomycin', sensitive: false },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">الأحياء الدقيقة</h1>
      <p className="text-sm text-neutral-500 -mt-5">إدارة زراعة الميكروبات وحساسية المضادات الحيوية</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {cultures.map(culture => (
          <Card key={culture.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm">{culture.sampleId}</span>
                <span className={cn(
                  'px-2 py-0.5 rounded text-[9px] font-bold',
                  culture.status === 'final' ? 'bg-success-50 text-success-600' :
                  culture.status === 'preliminary' ? 'bg-warning-50 text-warning-600' :
                  'bg-neutral-100 text-neutral-500',
                )}>
                  {culture.status === 'final' ? 'نهائي' : culture.status === 'preliminary' ? 'أولي' : 'معلق'}
                </span>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">المريض</span>
                <span className="font-bold">{culture.patient}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">الكائن</span>
                <span className={cn('font-bold', culture.organism === 'Pending' ? 'text-neutral-400' : 'text-neutral-900 dark:text-neutral-100')}>{culture.organism}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">النمو</span>
                <span className="font-bold">
                  {culture.growth === 'heavy' ? 'كثيف' : culture.growth === 'moderate' ? 'متوسط' : culture.growth === 'light' ? 'خفيف' : 'لا يوجد'}
                </span>
              </div>

              <div className="pt-3 border-t border-neutral-100 dark:border-neutral-700">
                <p className="text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-2">مضادات حيوية</p>
                <div className="space-y-1.5">
                  {antibiotics.map(ab => (
                    <div key={ab.name} className="flex items-center justify-between text-xs">
                      <span>{ab.name}</span>
                      <span className={cn(
                        'px-1.5 py-0.5 rounded font-bold',
                        ab.sensitive ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600',
                      )}>
                        {ab.sensitive ? 'S' : 'R'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button type="button" className="flex-1 py-2 bg-primary-500 text-white rounded-xl text-xs font-bold hover:bg-primary-600">تحديث النتيجة</button>
                <button type="button" className="px-3 py-2 bg-neutral-100 dark:bg-neutral-700 rounded-xl text-xs font-bold hover:bg-neutral-200">تقرير AST</button>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
}
