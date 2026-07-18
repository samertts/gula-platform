import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function Molecular() {
  const [results] = useState([
    { id: 'MOL-001', sampleId: 'SMP-8810', patient: 'Layla Hassan', target: 'SARS-CoV-2', method: 'rt_pcr', result: 'positive', ctValue: 28.5, status: 'final' },
    { id: 'MOL-002', sampleId: 'SMP-8822', patient: 'Omar Ismail', target: 'HBV DNA', method: 'pcr', result: 'negative', status: 'final' },
    { id: 'MOL-003', sampleId: 'SMP-8831', patient: 'Noor Ahmed', target: 'HCV RNA', method: 'rt_pcr', result: 'indeterminate', status: 'preliminary' },
    { id: 'MOL-004', sampleId: 'SMP-8845', patient: 'Zainab Kareem', target: 'MRSA', method: 'pcr', result: 'positive', ctValue: 22.1, status: 'final' },
  ]);

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">التشخيص الجزيئي</h1>
          <p className="text-sm text-neutral-500 mt-1">نتائج PCR والفحوصات الجزيئية</p>
        </div>
        <button type="button" className="px-4 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">
          تسجيل نتيجة جديدة
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {results.map(r => (
          <Card key={r.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-neutral-500">{r.sampleId}</span>
                <span className={cn(
                  'px-2 py-0.5 rounded text-[9px] font-bold',
                  r.result === 'positive' ? 'bg-danger-50 text-danger-600' :
                  r.result === 'negative' ? 'bg-success-50 text-success-600' :
                  'bg-warning-50 text-warning-600',
                )}>
                  {r.result === 'positive' ? 'إيجابي' : r.result === 'negative' ? 'سلبي' : 'غير محدد'}
                </span>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">المريض</span>
                <span className="font-bold">{r.patient}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">الهدف</span>
                <span className="font-bold">{r.target}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">الطريقة</span>
                <span className="font-bold">{r.method === 'rt_pcr' ? 'RT-PCR' : r.method === 'pcr' ? 'PCR' : r.method}</span>
              </div>
              {r.ctValue && (
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-500">Ct Value</span>
                  <span className="font-bold font-mono">{r.ctValue}</span>
                </div>
              )}
              <div className="pt-2">
                <button type="button" className="w-full py-2 bg-primary-500 text-white rounded-xl text-xs font-bold hover:bg-primary-600">عرض التفاصيل</button>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
}
