import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function Reports() {
  const [reportType, setReportType] = useState<'cumulative' | 'daily' | 'monthly'>('daily');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });

  const reportCategories = [
    { id: 'daily', label: 'تقارير يومية', icon: '📊', reports: ['سجل العينات اليومي', 'تقرير الفحوصات المنجزة', 'تقرير القيم الحرجة', 'تقرير مراقبة الجودة'] },
    { id: 'monthly', label: 'تقارير شهرية', icon: '📈', reports: ['إحصائية العينات الشهرية', 'تقرير الأداء', 'تقرير المخزون', 'تحليل TAT'] },
    { id: 'cumulative', label: 'تقارير تراكمية', icon: '📋', reports: ['تقرير مريض تراكمي', 'تحليل اتجاهات', 'تقرير جودة شامل', 'تقرير أجهزة'] },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">التقارير</h1>
      <p className="text-sm text-neutral-500 -mt-5">إنشاء وتصدير تقارير المختبر</p>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-4">
          {reportCategories.map(cat => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setReportType(cat.id as any)}
              className={cn(
                'w-full text-right p-4 rounded-2xl border-2 transition-all bg-white dark:bg-neutral-800',
                reportType === cat.id ? 'border-primary-500 shadow-sm' : 'border-neutral-200 dark:border-neutral-700',
              )}
            >
              <span className="text-lg mb-2 block">{cat.icon}</span>
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{cat.label}</p>
            </button>
          ))}
        </div>

        <div className="lg:col-span-3 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-4">
                <div className="flex gap-2">
                  <input type="date" value={dateRange.from} onChange={e => setDateRange(d => ({ ...d, from: e.target.value }))} className="px-4 py-2 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm bg-white dark:bg-neutral-800" />
                  <input type="date" value={dateRange.to} onChange={e => setDateRange(d => ({ ...d, to: e.target.value }))} className="px-4 py-2 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm bg-white dark:bg-neutral-800" />
                </div>
                <button type="button" className="px-4 py-2 bg-primary-500 text-white rounded-xl font-bold text-xs hover:bg-primary-600">تطبيق</button>
              </div>
            </CardHeader>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reportCategories.find(c => c.id === reportType)?.reports.map((report, i) => (
              <Card key={i} className="hover:shadow-md transition-shadow cursor-pointer">
                <CardBody className="flex items-center justify-between">
                  <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{report}</span>
                  <div className="flex gap-2">
                    <button type="button" className="px-3 py-1.5 bg-primary-50 text-primary-600 rounded-xl text-[10px] font-bold hover:bg-primary-100">PDF</button>
                    <button type="button" className="px-3 py-1.5 bg-success-50 text-success-600 rounded-xl text-[10px] font-bold hover:bg-success-100">CSV</button>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
