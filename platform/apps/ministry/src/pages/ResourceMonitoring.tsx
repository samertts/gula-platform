import { useState, useEffect } from 'react';
import { Card, Table, Badge, LoadingSpinner } from '@gula/ui-platform';
import { ChartWidget } from '../components/ChartWidget';

export function ResourceMonitoring() {
  const [loading, setLoading] = useState(true);
  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);
  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div><h1 className="text-2xl font-bold text-white">مراقبة الموارد</h1><p className="text-slate-400">مراقبة الموارد الصحية على المستوى الوطني</p></div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><div className="text-3xl font-bold">٨٧٪</div><div className="text-sm text-green-400">الأجهزة الطبية</div></Card>
        <Card><div className="text-3xl font-bold">٦٢٪</div><div className="text-sm text-yellow-400">المستلزمات</div></Card>
        <Card><div className="text-3xl font-bold">٩١٪</div><div className="text-sm text-green-400">الأدوية الأساسية</div></Card>
        <Card><div className="text-3xl font-bold">٤٥٪</div><div className="text-sm text-red-400">الموارد البشرية</div></Card>
      </div>

      <Card title="حالة الموارد حسب المحافظة">
        <Table
          columns={[{ key: 'resource', label: 'المورد' }, { key: 'level', label: 'المستوى' }, { key: 'status', label: 'الحالة' }]}
          data={[
            { resource: 'الأوكسجين', level: 'كبير', status: <Badge variant="success">متوفر</Badge> },
            { resource: 'المحاليل الوريدية', level: 'متوسط', status: <Badge variant="warning">تحذير</Badge> },
            { resource: 'أكياس الدم', level: 'منخفض', status: <Badge variant="danger">عجز</Badge> },
          ]}
        />
      </Card>
    </div>
  );
}
