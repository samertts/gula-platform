import { useState, useEffect } from 'react';
import { Card, Table, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function HospitalStatistics() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">إحصاءات المستشفيات</h1><p className="text-slate-400">مؤشرات أداء المستشفيات الوطنية</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold">٣٤٧</div><div className="text-sm text-slate-400">إجمالي المستشفيات</div></Card>
        <Card><div className="text-3xl font-bold text-green-400">٦٨٪</div><div className="text-sm text-slate-400">معدل الإشغال</div></Card>
        <Card><div className="text-3xl font-bold text-blue-400">٨٩٢</div><div className="text-sm text-slate-400">أسرة العناية المركزة</div></Card>
        <Card><div className="text-3xl font-bold text-yellow-400">٤.٢</div><div className="text-sm text-slate-400">متوسط الإقامة (أيام)</div></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartWidget title="معدلات الإشغال" type="line" />
        <ChartWidget title="توزيع الأسرة" type="pie" />
      </div>
    </div>
  );
}
