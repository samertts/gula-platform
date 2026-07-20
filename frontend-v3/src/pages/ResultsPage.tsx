import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { results, orders } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { useTranslation } from 'react-i18next';
import { formatDateTime } from '@/lib/utils';
import type { LabResult } from '@/types/backend';
import { TestTubes, Plus, CheckCircle } from 'lucide-react';

export function ResultsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ order_id: '', test_name: '', value: '', value_text: '', unit: '' });

  const { data: ordersData } = useQuery({
    queryKey: ['orders-dropdown'],
    queryFn: () => orders.list({ limit: 100 }),
  });

  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);

  const { data: orderDetail } = useQuery({
    queryKey: ['order', selectedOrderId],
    queryFn: () => orders.get(selectedOrderId!),
    enabled: !!selectedOrderId,
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => results.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order'] });
      setShowCreate(false);
      setForm({ order_id: '', test_name: '', value: '', value_text: '', unit: '' });
    },
  });

  const verifyMutation = useMutation({
    mutationFn: (id: number) => results.verify(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order'] });
    },
  });

  const columns: Column<LabResult>[] = [
    { key: 'id', header: 'ID' },
    { key: 'test_name', header: t('testName'), sortable: true },
    { key: 'value', header: t('resultValue'), render: (r) => r.value ?? r.value_text ?? '—' },
    { key: 'unit', header: t('unit') },
    { key: 'flag', header: t('resultFlag'), render: (r) => r.flag ? <StatusBadge status={r.flag} /> : '—' },
    { key: 'created_at', header: t('date'), render: (r) => formatDateTime(r.created_at) },
    {
      key: 'actions', header: t('actions'),
      render: (r) => (
        <Button size="sm" variant="ghost" onClick={() => verifyMutation.mutate(r.id)}>
          <CheckCircle className="h-4 w-4" />
          {t('verifyResult')}
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">{t('results')}</h1>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          {t('addResult')}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="rounded-xl border border-outline bg-surface p-4">
            <h3 className="font-semibold text-on-surface mb-3">{t('orders')}</h3>
            <div className="space-y-1">
              {ordersData?.items?.slice(0, 20).map((o) => (
                <button
                  key={o.id}
                  onClick={() => setSelectedOrderId(o.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedOrderId === o.id ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-surface-container-high'
                  }`}
                >
                  <span className="block font-medium">Order #{o.id}</span>
                  <span className="block text-xs text-on-surface-variant">{o.status} — {formatDateTime(o.created_at)}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          {orderDetail ? (
            <div className="rounded-xl border border-outline bg-surface">
              <div className="px-5 py-4 border-b border-outline">
                <h3 className="font-semibold text-on-surface">
                  {t('results')} — Order #{orderDetail.id}
                </h3>
                <p className="text-sm text-on-surface-variant">{orderDetail.patient?.full_name}</p>
              </div>
              <div className="p-4">
                <DataTable
                  columns={columns}
                  data={orderDetail.results || []}
                  keyExtractor={(r) => r.id}
                  emptyTitle={t('noData')}
                  emptyDescription={t('addResult')}
                />
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-outline bg-surface p-8 text-center">
              <TestTubes className="h-12 w-12 text-on-surface-variant mx-auto mb-3" />
              <p className="text-on-surface-variant">{t('selectOrder', 'اختر طلباً لعرض النتائج')}</p>
            </div>
          )}
        </div>
      </div>

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title={t('addResult')}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ order_id: Number(form.order_id), test_name: form.test_name, value: form.value ? Number(form.value) : undefined, value_text: form.value_text || undefined, unit: form.unit || undefined }); }} className="space-y-4">
          <Input label="Order ID" type="number" value={form.order_id} onChange={(e) => setForm({ ...form, order_id: e.target.value })} required />
          <Input label={t('testName')} value={form.test_name} onChange={(e) => setForm({ ...form, test_name: e.target.value })} required />
          <div className="grid grid-cols-2 gap-4">
            <Input label={t('resultValue')} type="number" step="any" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
            <Input label={t('valueText', 'نص النتيجة')} value={form.value_text} onChange={(e) => setForm({ ...form, value_text: e.target.value })} />
          </div>
          <Input label={t('unit')} value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          <div className="flex gap-4 justify-end pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>{t('cancel')}</Button>
            <Button type="submit" isLoading={createMutation.isPending}>{t('create')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
