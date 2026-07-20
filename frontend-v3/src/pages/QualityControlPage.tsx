import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { qualityControl } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { useTranslation } from 'react-i18next';
import { formatDateTime } from '@/lib/utils';
import type { QualityControl, QCStatus } from '@/types/backend';
import { Shield, Plus, BarChart3 } from 'lucide-react';

export function QualityControlPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [showSubmit, setShowSubmit] = useState(false);
  const [form, setForm] = useState({
    test_code: '', instrument_name: '', lot_number: '', level: 'normal',
    expected_value: '', measured_value: '', sd: '', unit: '', notes: '', performed_by: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['qc', page],
    queryFn: () => qualityControl.list({ skip: page * 20, limit: 20 }),
  });

  const { data: summary } = useQuery({
    queryKey: ['qc-summary'],
    queryFn: () => qualityControl.summary(),
  });

  const submitMutation = useMutation({
    mutationFn: (data: any) => qualityControl.submit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qc'] });
      queryClient.invalidateQueries({ queryKey: ['qc-summary'] });
      setShowSubmit(false);
    },
  });

  const columns: Column<QualityControl>[] = [
    { key: 'test_code', header: t('testCode'), sortable: true },
    { key: 'instrument_name', header: t('instrument') },
    { key: 'level', header: t('level', 'المستوى') },
    { key: 'expected_value', header: t('expected', 'متوقع'), render: (q) => q.expected_value },
    { key: 'measured_value', header: t('measured', 'مقيس'), render: (q) => q.measured_value },
    { key: 'status', header: t('status'), render: (q) => <StatusBadge status={q.status} /> },
    { key: 'violation', header: 'Violation' },
    { key: 'created_at', header: t('date'), render: (q) => formatDateTime(q.created_at) },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">{t('qualityControl')}</h1>
          <p className="text-on-surface-variant mt-1">{t('total')}: {data?.total ?? 0}</p>
        </div>
        <Button onClick={() => setShowSubmit(true)}>
          <Plus className="h-4 w-4" />
          {t('submit', 'تقديم')}
        </Button>
      </div>

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {Object.entries(summary).map(([key, val]: [string, any]) => (
            <div key={key} className="rounded-xl border border-outline bg-surface p-5">
              <p className="text-sm text-on-surface-variant">{key}</p>
              <p className="text-2xl font-bold text-on-surface mt-1">
                {typeof val === 'object' ? JSON.stringify(val) : val}
              </p>
            </div>
          ))}
        </div>
      )}

      <DataTable
        columns={columns}
        data={data?.items || []}
        keyExtractor={(q) => q.id}
        isLoading={isLoading}
        searchable
        searchKeys={['test_code', 'instrument_name', 'violation']}
        emptyTitle={t('noData')}
      />

      <Modal isOpen={showSubmit} onClose={() => setShowSubmit(false)} title={t('submit', 'تقديم نتيجة QC')}>
        <form onSubmit={(e) => { e.preventDefault(); submitMutation.mutate({ ...form, expected_value: Number(form.expected_value), measured_value: Number(form.measured_value), sd: form.sd ? Number(form.sd) : undefined }); }} className="space-y-4">
          <Input label={t('testCode')} value={form.test_code} onChange={(e) => setForm({ ...form, test_code: e.target.value })} required />
          <Input label={t('instrument')} value={form.instrument_name} onChange={(e) => setForm({ ...form, instrument_name: e.target.value })} />
          <Input label={t('lotNumber')} value={form.lot_number} onChange={(e) => setForm({ ...form, lot_number: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <Input label={t('expected', 'القيمة المتوقعة')} type="number" step="any" value={form.expected_value} onChange={(e) => setForm({ ...form, expected_value: e.target.value })} required />
            <Input label={t('measured', 'القيمة المقاسة')} type="number" step="any" value={form.measured_value} onChange={(e) => setForm({ ...form, measured_value: e.target.value })} required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="SD" type="number" step="any" value={form.sd} onChange={(e) => setForm({ ...form, sd: e.target.value })} />
            <Input label={t('unit')} value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          </div>
          <Input label={t('notes')} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <Input label={t('performedBy', 'بواسطة')} value={form.performed_by} onChange={(e) => setForm({ ...form, performed_by: e.target.value })} />
          <div className="flex gap-4 justify-end pt-2">
            <Button variant="ghost" onClick={() => setShowSubmit(false)}>{t('cancel')}</Button>
            <Button type="submit" isLoading={submitMutation.isPending}>{t('submit')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
