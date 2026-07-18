import { useState, useEffect } from 'react';
import { Card, Table, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function BirthRegistration() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">تسجيل المواليد</h1><p className="text-slate-400">إحصاءات تسجيل المواليد الوطني</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold">١٠٬٢٣٤</div><div className="text-sm text-slate-400">مواليد هذا الشهر</div></Card>
        <Card><div className="text-3xl font-bold text-green-400">٩٨٪</div><div className="text-sm text-slate-400">نسبة التسجيل</div></Card>
        <Card><div className="text-3xl font-bold text-blue-400">٥٬١١٢</div><div className="text-sm text-slate-400">ذكور</div></Card>
        <Card><div className="text-3xl font-bold text-pink-400">٥٬١٢٢</div><div className="text-sm text-slate-400">إناث</div></Card>
      </div>

      <ChartWidget title="المواليد حسب المحافظة" type="bar" />
    </div>
  );
}
