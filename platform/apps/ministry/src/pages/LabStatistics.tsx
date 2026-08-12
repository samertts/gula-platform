import { useState, useEffect } from 'react';
import { Card, Table, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function LabStatistics() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">إحصاءات المختبرات</h1><p className="text-slate-400">إحصاءات شاملة للمختبرات الوطنية</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold">١٢,٤٥١</div><div className="text-sm text-slate-400">إجمالي المختبرات</div></Card>
        <Card><div className="text-3xl font-bold text-green-400">٨,٩٢٣</div><div className="text-sm text-slate-400">مختبرات حكومية</div></Card>
        <Card><div className="text-3xl font-bold text-blue-400">٣,٥٢٨</div><div className="text-sm text-slate-400">مختبرات خاصة</div></Card>
        <Card><div className="text-3xl font-bold text-yellow-400">٤٥٢</div><div className="text-sm text-slate-400">مختبرات متنقلة</div></Card>
      </div>

      <Card title="إجمالي الفحوصات الشهرية">
        <ChartWidget title="الفحوصات حسب النوع" type="bar" />
      </Card>

      <Card title="المختبرات حسب المحافظة">
        <Table
          columns={[{ key: 'region', label: 'المحافظة' }, { key: 'gov', label: 'حكومي' }, { key: 'private', label: 'خاص' }, { key: 'total', label: 'المجموع' }]}
          data={[
            { region: 'بغداد', gov: 1240, private: 890, total: 2130 },
            { region: 'البصرة', gov: 420, private: 310, total: 730 },
            { region: 'نينوى', gov: 380, private: 210, total: 590 },
          ]}
        />
      </Card>
    </div>
  );
}
