import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orders, patients } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { formatDateTime, paginationParams } from '@/lib/utils';
import type { LabOrder } from '@/types/backend';
import { ClipboardList, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function OrdersPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ patient_id: '', doctor_name: '', test_codes: '' });

  const { data, isLoading } = useQuery({
    queryKey: ['orders', page],
    queryFn: () => orders.list(paginationParams(page * 20, 20)),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => orders.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      setShowCreate(false);
    },
  });

  const validateMutation = useMutation({
    mutationFn: (id: number) => orders.validate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => orders.cancel(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  });

  const columns: Column<LabOrder>[] = [
    { key: 'id', header: t('code', 'رقم'), render: (o) => `#${o.id}` },
    {
      key: 'patient_id', header: t('patientId'),
      render: (o) => o.patient?.full_name || `#${o.patient_id}`,
    },
    { key: 'doctor_name', header: t('doctorName') },
    {
      key: 'status', header: t('status'),
      render: (o) => <StatusBadge status={o.status} />,
    },
    { key: 'created_at', header: t('date'), render: (o) => formatDateTime(o.created_at) },
    {
      key: 'actions', header: t('actions'),
      render: (o) => (
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => navigate(`/orders/${o.id}`)}>{t('details', 'عرض')}</Button>
          {o.status === 'pending' && (
            <>
              <Button size="sm" variant="ghost" onClick={() => validateMutation.mutate(o.id)}>{t('validateOrder', 'توثيق')}</Button>
              <Button size="sm" variant="ghost" className="text-error" onClick={() => cancelMutation.mutate(o.id)}>{t('cancelOrder', 'إلغاء')}</Button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">{t('orders')}</h1>
          <p className="text-on-surface-variant mt-1">{t('total')}: {data?.total ?? 0}</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          {t('addOrder')}
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items || []}
        keyExtractor={(o) => o.id}
        isLoading={isLoading}
        searchable
        searchKeys={['doctor_name']}
        emptyTitle={t('noData')}
      />

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title={t('addOrder')}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ patient_id: Number(form.patient_id), doctor_name: form.doctor_name, tests: form.test_codes.split(',').map((c) => ({ test_code: c.trim(), test_name: c.trim() })) }); }} className="space-y-4">
          <Input label={t('patientId')} value={form.patient_id} onChange={(e) => setForm({ ...form, patient_id: e.target.value })} required />
          <Input label={t('doctorName')} value={form.doctor_name} onChange={(e) => setForm({ ...form, doctor_name: e.target.value })} />
          <Input label={t('testCode', 'رموز الفحوصات (مفصولة بفواصل)')} value={form.test_codes} onChange={(e) => setForm({ ...form, test_codes: e.target.value })} placeholder="CBC, TSH, HbA1c" />
          <div className="flex gap-4 justify-end pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>{t('cancel')}</Button>
            <Button type="submit" isLoading={createMutation.isPending}>{t('create')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
