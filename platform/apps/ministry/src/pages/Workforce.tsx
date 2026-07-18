import { useState, useEffect } from 'react';
import { Card, Table, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function Workforce() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">القوى العاملة الصحية</h1><p className="text-slate-400">توزيع الكوادر الصحية في العراق</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold">٢٥٢٬٠٠٠</div><div className="text-sm text-slate-400">إجمالي الكوادر</div></Card>
        <Card><div className="text-3xl font-bold">٧٨٬٠٠٠</div><div className="text-sm text-slate-400">أطباء</div></Card>
        <Card><div className="text-3xl font-bold">١٢٠٬٠٠٠</div><div className="text-sm text-slate-400">ممرضين</div></Card>
        <Card><div className="text-3xl font-bold">٣٤٣</div><div className="text-sm text-slate-400">لكل ١٠٠,٠٠٠ نسمة</div></Card>
      </div>

      <ChartWidget title="توزيع الكوادر حسب التخصص" type="pie" />
    </div>
  );
}
