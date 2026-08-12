import { useState, useEffect } from 'react';
import { Card, Table, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function VaccinationCoverage() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">التغطية التطعيمية</h1><p className="text-slate-400">مؤشرات التطعيم الوطني</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold text-green-400">٨٧٪</div><div className="text-sm text-slate-400">التغطية الإجمالية</div></Card>
        <Card><div className="text-3xl font-bold">٩٢٪</div><div className="text-sm text-slate-400">شلل الأطفال</div></Card>
        <Card><div className="text-3xl font-bold text-yellow-400">٧٨٪</div><div className="text-sm text-slate-400">الحصبة</div></Card>
        <Card><div className="text-3xl font-bold text-green-400">٩٥٪</div><div className="text-sm text-slate-400">BCG</div></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartWidget title="التغطية حسب اللقاح" type="bar" />
        <ChartWidget title="الاتجاه السنوي" type="line" />
      </div>
    </div>
  );
}
