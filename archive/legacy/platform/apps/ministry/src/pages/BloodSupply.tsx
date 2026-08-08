import { useState, useEffect } from 'react';
import { Card, Table, Badge, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function BloodSupply() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">إمداد الدم الوطني</h1><p className="text-slate-400">مراقبة مخزون الدم ومراكز التبرع</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold text-red-500">4,500</div><div className="text-sm text-slate-400">كيس دم متاح</div></Card>
        <Card><div className="text-3xl font-bold text-green-400">٢٣٠</div><div className="text-sm text-slate-400">متبرع اليوم</div></Card>
        <Card><div className="text-3xl font-bold text-yellow-400">٧</div><div className="text-sm text-slate-400">أيام المخزون</div></Card>
        <Card><div className="text-3xl font-bold text-blue-400">٤٥</div><div className="text-sm text-slate-400">مركز تبرع</div></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartWidget title="مخزون الدم حسب الفصيلة" type="bar" />
        <ChartWidget title="التبرع الشهري" type="line" />
      </div>
    </div>
  );
}
