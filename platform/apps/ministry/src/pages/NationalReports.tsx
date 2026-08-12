import { useState, useEffect } from 'react';
import { Card, Button, Select, Table, LoadingSpinner } from '@gula/ui-platform';
import { DataExport } from '../components/DataExport';

export function NationalReports() {
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState('monthly');
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white">التقارير الوطنية</h1><p className="text-slate-400">إنشاء وتصدير التقارير الصحية</p></div>
        <div className="flex gap-2">
          <Select value={reportType} onChange={e => setReportType(e.target.value)}
            options={[{ value: 'monthly', label: 'تقرير شهري' }, { value: 'quarterly', label: 'تقرير ربع سنوي' }, { value: 'annual', label: 'تقرير سنوي' }]} />
          <DataExport />
        </div>
      </div>

      <Card title="التقارير المتاحة">
        <Table
          columns={[{ key: 'name', label: 'اسم التقرير' }, { key: 'period', label: 'الفترة' }, { key: 'updated', label: 'آخر تحديث' }, { key: 'actions', label: '' }]}
          data={[
            { name: 'التقرير الصحي الشهري', period: 'يونيو ٢٠٢٦', updated: '٢٠٢٦-٠٧-١٥', actions: <Button size="sm">تحميل</Button> },
            { name: 'إحصاءات المختبرات', period: 'الربع الثاني ٢٠٢٦', updated: '٢٠٢٦-٠٧-٠١', actions: <Button size="sm">تحميل</Button> },
            { name: 'تقرير التطعيم الوطني', period: 'يونيو ٢٠٢٦', updated: '٢٠٢٦-٠٧-١٤', actions: <Button size="sm">تحميل</Button> },
          ]}
        />
      </Card>
    </div>
  );
}
