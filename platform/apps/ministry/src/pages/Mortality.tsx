import { useState, useEffect } from 'react';
import { Card, Table, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function Mortality() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">إحصاءات الوفيات</h1><p className="text-slate-400">بيانات الوفيات والتحليل</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold">١٢٬٤٥١</div><div className="text-sm text-slate-400">إجمالي الوفيات (شهري)</div></Card>
        <Card><div className="text-3xl font-bold text-red-400">٣٬٢٨٩</div><div className="text-sm text-slate-400">الأمراض القلبية</div></Card>
        <Card><div className="text-3xl font-bold text-yellow-400">٢٬١٥٤</div><div className="text-sm text-slate-400">السرطان</div></Card>
        <Card><div className="text-3xl font-bold text-blue-400">٤٥٦</div><div className="text-sm text-slate-400">حوادث السير</div></Card>
      </div>

      <ChartWidget title="أسباب الوفيات" type="pie" />
    </div>
  );
}
