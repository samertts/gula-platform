import { useState, useEffect } from 'react';
import { Card, Badge, Button, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function EmergencyResponse() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">الاستجابة للطوارئ</h1><p className="text-slate-400">غرفة العمليات الوطنية للطوارئ</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-center"><div className="text-3xl font-bold text-red-400 text-4xl">٣</div><div className="text-sm text-slate-400">طوارئ نشطة</div></div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-yellow-400">١٢</div><div className="text-sm text-slate-400">فرق استجابة</div></div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-green-400">٤٥</div><div className="text-sm text-slate-400">سيارة إسعاف</div></div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-blue-400">٨٩٪</div><div className="text-sm text-slate-400">جاهزية</div></div></Card>
      </div>

      <Card title="حالات الطوارئ النشطة">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-red-900/20 rounded-lg">
            <div><span className="font-bold">فيضان</span><span className="text-sm text-slate-400 mr-2">ميسان</span></div>
            <Badge variant="danger">حرج</Badge>
          </div>
          <div className="flex items-center justify-between p-3 bg-yellow-900/20 rounded-lg">
            <div><span className="font-bold">حرائق</span><span className="text-sm text-slate-400 mr-2">كركوك</span></div>
            <Badge variant="warning">تحذير</Badge>
          </div>
          <div className="flex items-center justify-between p-3 bg-blue-900/20 rounded-lg">
            <div><span className="font-bold">حشد صحي</span><span className="text-sm text-slate-400 mr-2">بغداد</span></div>
            <Badge variant="info">مراقبة</Badge>
          </div>
        </div>
      </Card>
    </div>
  );
}
