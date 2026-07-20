import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { criticalAlerts } from '@/api/endpoints';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { useTranslation } from 'react-i18next';
import { formatDateTime } from '@/lib/utils';
import type { CriticalAlert } from '@/types/backend';
import { AlertTriangle } from 'lucide-react';

export function CriticalAlertsPage() {
  const { t } = useTranslation();
  const [hours, setHours] = useState(24);

  const { data, isLoading } = useQuery({
    queryKey: ['critical-alerts', hours],
    queryFn: () => criticalAlerts.list({ hours }),
  });

  const columns: Column<CriticalAlert>[] = [
    { key: 'test_name', header: t('testName'), sortable: true },
    { key: 'value', header: t('resultValue') },
    { key: 'flag', header: t('resultFlag'), render: (a) => <StatusBadge status={a.flag} className="bg-red-100 text-red-800" /> },
    { key: 'acknowledged', header: t('status'), render: (a) => <StatusBadge status={a.acknowledged ? 'completed' : 'pending'} /> },
    { key: 'created_at', header: t('date'), render: (a) => formatDateTime(a.created_at) },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-error" />
            {t('criticalAlerts', 'التنبيهات الحرجة')}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-on-surface-variant">{t('hours', 'الساعات')}:</label>
          <select
            className="h-10 rounded-lg border border-outline bg-surface px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
          >
            <option value={1}>1 {t('hours', 'ساعة')}</option>
            <option value={6}>6 {t('hours', 'ساعات')}</option>
            <option value={12}>12 {t('hours', 'ساعة')}</option>
            <option value={24}>24 {t('hours', 'ساعة')}</option>
            <option value={48}>48 {t('hours', 'ساعة')}</option>
            <option value={72}>72 {t('hours', 'ساعة')}</option>
          </select>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={data || []}
        keyExtractor={(a) => a.id}
        isLoading={isLoading}
        emptyTitle={t('noAlerts', 'لا توجد تنبيهات حرجة')}
        emptyDescription={t('noAlertsDesc', 'جميع النتائج ضمن الحدود الطبيعية')}
      />
    </div>
  );
}
