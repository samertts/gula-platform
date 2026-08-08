import { useState, useEffect } from 'react';
import { Card, LoadingSpinner } from '@gula/ui-platform';
import { MapView } from '../components/MapView';
import { RegionalTable } from '../components/RegionalTable';
import { ChartWidget } from '../components/ChartWidget';

export function RegionalAnalytics() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">التحليلات الإقليمية</h1><p className="text-slate-400">تحليلات صحية حسب المحافظة والمنطقة</p></div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="خريطة العراق الصحية"><MapView /></Card>
        <div className="space-y-6">
          <ChartWidget title="المقارنة بين المحافظات" type="bar" />
          <ChartWidget title="النمو السنوي" type="line" />
        </div>
      </div>

      <Card title="إحصاءات المحافظات">
        <RegionalTable />
      </Card>
    </div>
  );
}
