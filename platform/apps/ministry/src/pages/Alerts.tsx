import { useState, useEffect } from 'react';
import { Card, Badge, Button, LoadingSpinner } from '@gula/ui-platform';
import { AlertPanel } from '../components/AlertPanel';
import { alertsService } from '../services/alerts';

export function Alerts() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { alertsService.getAlerts().then(a => { setAlerts(a); setLoading(false); }).catch(() => setLoading(false)); }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white">الإنذارات الوطنية</h1><p className="text-slate-400">إنذارات وتنبيهات النظام الصحي</p></div>
        <Button variant="danger">تفعيل الإنذار العام</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><div className="text-center"><div className="text-3xl font-bold text-red-400">٣</div><div className="text-sm text-slate-400">حرجة</div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-yellow-400">٧</div><div className="text-sm text-slate-400">تحذيرية</div></Card>
        <Card><div className="text-center"><div className="text-3xl font-bold text-blue-400">١٢</div><div className="text-sm text-slate-400">معلوماتية</div></Card>
      </div>

      <AlertPanel />
    </div>
  );
}
