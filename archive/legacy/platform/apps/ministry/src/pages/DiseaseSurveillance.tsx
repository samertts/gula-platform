import { useState, useEffect } from 'react';
import { Card, Badge, Table, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';
import { RegionalTable } from '../components/RegionalTable';
import { surveillanceService } from '../services/surveillance';

export function DiseaseSurveillance() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { surveillanceService.getDiseaseData().then(d => { setData(d); setLoading(false); }).catch(() => setLoading(false)); }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">الترصد الوبائي</h1><p className="text-slate-400">مراقبة الأمراض السارية والمعدية</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-center"><div className="text-3xl font-bold text-red-400">٢٤٣</div><div className="text-sm text-slate-400">الحالات النشطة</div></div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-yellow-400">٣٧</div><div className="text-sm text-slate-400">حالات مشبوهة</div></div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-green-400">١,٨٩٢</div><div className="text-sm text-slate-400">حالات متعافية</div></div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-blue-400">١٢</div><div className="text-sm text-slate-400">حالات وفاة</div></div></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartWidget title="اتجاهات الأمراض" type="line" />
        <ChartWidget title="توزيع الأمراض" type="pie" />
      </div>

      <Card title="حالات التفشي النشطة">
        <RegionalTable />
      </Card>

      <Card title="الإبلاغات الأخيرة">
        <Table
          columns={[{ key: 'disease', label: 'المرض' }, { key: 'region', label: 'المحافظة' }, { key: 'cases', label: 'الحالات' }, { key: 'status', label: 'الحالة' }]}
          data={[
            { disease: 'كوليرا', region: 'بغداد', cases: 45, status: 'نشط' },
            { disease: 'حصبة', region: 'نينوى', cases: 23, status: 'تحت السيطرة' },
            { disease: 'حمى الضنك', region: 'البصرة', cases: 12, status: 'مراقبة' },
          ]}
        />
      </Card>
    </div>
  );
}
