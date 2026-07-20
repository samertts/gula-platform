import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { admin } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { formatDateTime, paginationParams } from '@/lib/utils';
import type { Lab } from '@/types/backend';
import { Building2, Plus } from 'lucide-react';

export function AdminLabsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '', lab_type: '', city: '', address: '', phone: '',
    admin_email: '', admin_name: '', admin_password: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['admin-labs', page],
    queryFn: () => admin.labs.list(paginationParams(page * 20, 20)),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => admin.labs.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-labs'] });
      setShowCreate(false);
    },
  });

  const columns: Column<Lab>[] = [
    { key: 'name', header: t('labName'), sortable: true },
    { key: 'lab_type', header: t('labType') },
    { key: 'city', header: t('city') },
    { key: 'phone', header: t('phone') },
    { key: 'is_active', header: t('status'), render: (l) => <StatusBadge status={l.is_active ? 'active' : 'inactive'} /> },
    { key: 'created_at', header: t('date'), render: (l) => formatDateTime(l.created_at) },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">{t('labs')}</h1>
          <p className="text-on-surface-variant mt-1">{t('total')}: {data?.total ?? 0}</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          {t('addLab', 'إضافة مختبر')}
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items || []}
        keyExtractor={(l) => l.id}
        isLoading={isLoading}
        searchable
        searchKeys={['name', 'city', 'phone']}
        emptyTitle={t('noData')}
      />

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title={t('addLab', 'إضافة مختبر')}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }} className="space-y-4">
          <Input label={t('labName')} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <Input label={t('labType')} value={form.lab_type} onChange={(e) => setForm({ ...form, lab_type: e.target.value })} />
          <Input label={t('city')} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          <Input label={t('address')} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Input label={t('phone')} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <hr className="border-outline" />
          <p className="text-sm font-medium text-on-surface">{t('adminInfo', 'معلومات المسؤول')}</p>
          <Input label={t('adminName', 'اسم المسؤول')} value={form.admin_name} onChange={(e) => setForm({ ...form, admin_name: e.target.value })} required />
          <Input label={t('email')} type="email" value={form.admin_email} onChange={(e) => setForm({ ...form, admin_email: e.target.value })} required />
          <Input label={t('password')} type="password" value={form.admin_password} onChange={(e) => setForm({ ...form, admin_password: e.target.value })} required />
          <div className="flex gap-4 justify-end pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>{t('cancel')}</Button>
            <Button type="submit" isLoading={createMutation.isPending}>{t('create')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
