import { useState, useEffect } from 'react';
import { Card, Table, Badge, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function MedicationSupply() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">سلسلة الإمداد الدوائي</h1><p className="text-slate-400">مراقبة توفر الأدوية على المستوى الوطني</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold text-green-400">٨٧٪</div><div className="text-sm text-slate-400">توفر الأدوية الأساسية</div></Card>
        <Card><div className="text-3xl font-bold text-yellow-400">٦٥٪</div><div className="text-sm text-slate-400">توفر الأدوية المتخصصة</div></Card>
        <Card><div className="text-3xl font-bold">٢٣٤</div><div className="text-sm text-slate-400">دواء ناقص</div></Card>
        <Card><div className="text-3xl font-bold text-red-400">٤٥</div><div className="text-sm text-slate-400">دواء منقطع</div></Card>
      </div>

      <Card title="الأدوية منخفضة التوفر">
        <Table
          columns={[{ key: 'drug', label: 'الدواء' }, { key: 'level', label: 'المستوى' }, { key: 'region', label: 'المحافظة' }, { key: 'status', label: 'الحالة' }]}
          data={[
            { drug: 'أنسولين', level: '٢٥٪', region: 'بغداد', status: <Badge variant="danger">عجز</Badge> },
            { drug: 'أموكسيسيلين', level: '٤٥٪', region: 'نينوى', status: <Badge variant="warning">ناقص</Badge> },
            { drug: 'أتروبين', level: '١٠٪', region: 'البصرة', status: <Badge variant="danger">حرج</Badge> },
          ]}
        />
      </Card>
    </div>
  );
}
