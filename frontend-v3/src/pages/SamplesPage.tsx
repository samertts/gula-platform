import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { samples } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { useTranslation } from 'react-i18next';
import { formatDateTime, paginationParams } from '@/lib/utils';
import type { Sample } from '@/types/backend';
import { FlaskConical, Plus } from 'lucide-react';

export function SamplesPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ order_id: '', sample_type: 'blood', collected_by: '', notes: '' });

  const { data, isLoading } = useQuery({
    queryKey: ['samples', page],
    queryFn: () => samples.list(paginationParams(page * 20, 20)),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => samples.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      setShowCreate(false);
      setForm({ order_id: '', sample_type: 'blood', collected_by: '', notes: '' });
    },
  });

  const columns: Column<Sample>[] = [
    { key: 'barcode', header: t('barcode'), sortable: true },
    {
      key: 'sample_type', header: t('sampleType'),
      render: (s) => <StatusBadge status={s.sample_type} />,
    },
    { key: 'status', header: t('status'), render: (s) => <StatusBadge status={s.status} /> },
    { key: 'collected_by', header: t('collectedBy') },
    { key: 'collection_time', header: t('collectionDate'), render: (s) => formatDateTime(s.collection_time) },
    { key: 'storage_location', header: t('storageLocation') },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">{t('samples')}</h1>
          <p className="text-on-surface-variant mt-1">{t('total')}: {data?.total ?? 0}</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          {t('addSample')}
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items || []}
        keyExtractor={(s) => s.id}
        isLoading={isLoading}
        searchable
        searchKeys={['barcode', 'sample_type', 'collected_by']}
        emptyTitle={t('noData')}
      />

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title={t('addSample')}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }} className="space-y-4">
          <Input label="Order ID" type="number" value={form.order_id} onChange={(e) => setForm({ ...form, order_id: e.target.value })} required />
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-on-surface">{t('sampleType')}</label>
            <select className="flex h-10 w-full rounded-lg border border-outline bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40" value={form.sample_type} onChange={(e) => setForm({ ...form, sample_type: e.target.value })}>
              <option value="blood">Blood</option>
              <option value="urine">Urine</option>
              <option value="stool">Stool</option>
              <option value="swab">Swab</option>
              <option value="serum">Serum</option>
              <option value="plasma">Plasma</option>
              <option value="csf">CSF</option>
              <option value="sputum">Sputum</option>
              <option value="other">Other</option>
            </select>
          </div>
          <Input label={t('collectedBy')} value={form.collected_by} onChange={(e) => setForm({ ...form, collected_by: e.target.value })} />
          <Input label={t('notes')} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <div className="flex gap-4 justify-end pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>{t('cancel')}</Button>
            <Button type="submit" isLoading={createMutation.isPending}>{t('create')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
