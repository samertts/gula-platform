import { useState, useEffect } from 'react';
import { Card, LoadingSpinner } from '@gula/ui-platform';
import { KPICard } from '../components/KPICard';
import { ChartWidget } from '../components/ChartWidget';
import { AlertPanel } from '../components/AlertPanel';
import { statisticsService } from '../services/statistics';

export function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    statisticsService.getAggregated().then(data => { setStats(data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div>
        <h1 className="text-2xl font-bold text-white">لوحة القيادة الوطنية</h1>
        <p className="text-slate-400">نظرة شاملة على النظام الصحي في العراق</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="إجمالي المستشفيات" value="1,247" trend="+3.2%" icon="Building2" />
        <KPICard title="إجمالي المختبرات" value="3,891" trend="+5.1%" icon="Microscope" />
        <KPICard title="المرضى المسجلين" value="24.5M" trend="+8.7%" icon="Users" />
        <KPICard title="الفحوصات اليوم" value="142,389" trend="+2.3%" icon="FlaskConical" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartWidget title="المؤشرات الصحية الرئيسية" type="line" />
        <ChartWidget title="توزيع الموارد حسب المحافظة" type="bar" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="حالة النظام">
          <div className="space-y-2">
            <div className="flex justify-between"><span>وقت التشغيل</span><span className="text-green-400">٩٩.٩٧٪</span></div>
            <div className="flex justify-between"><span>زمن الاستجابة</span><span className="text-green-400">٢٣٤ مللي ثانية</span></div>
            <div className="flex justify-between"><span>الطلبات/ثانية</span><span className="text-blue-400">١,٢٤٧</span></div>
          </div>
        </Card>
        <Card title="الأجهزة المتصلة">
          <div className="space-y-2">
            <div className="flex justify-between"><span>أجهزة التحليل</span><span className="text-green-400">٤,٢٣١ متصل</span></div>
            <div className="flex justify-between"><span>محطات العمل</span><span className="text-green-400">١٢,٨٤٧ متصل</span></div>
            <div className="flex justify-between"><span>أجهزة محمولة</span><span className="text-yellow-400">٨٩٣ غير متصل</span></div>
          </div>
        </Card>
        <AlertPanel />
      </div>
    </div>
  );
}
