import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { admin } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Modal } from '@/components/ui/Modal';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { formatDateTime, paginationParams } from '@/lib/utils';
import type { LabUser, UserRole } from '@/types/backend';
import { UserCog, Plus } from 'lucide-react';

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'admin', label: 'Admin' },
  { value: 'lab_admin', label: 'Lab Admin' },
  { value: 'doctor', label: 'Doctor' },
  { value: 'staff', label: 'Staff' },
  { value: 'technician', label: 'Technician' },
  { value: 'citizen', label: 'Citizen' },
];

export function AdminUsersPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'staff' as UserRole, lab_id: '' });

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', page],
    queryFn: () => admin.users.list(paginationParams(page * 20, 20)),
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => admin.users.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setShowCreate(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => admin.users.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  const columns: Column<LabUser>[] = [
    { key: 'name', header: t('name'), sortable: true },
    { key: 'email', header: t('email'), sortable: true },
    { key: 'role', header: t('role'), render: (u) => <StatusBadge status={u.role} /> },
    { key: 'is_active', header: t('status'), render: (u) => <StatusBadge status={u.is_active ? 'active' : 'inactive'} /> },
    { key: 'created_at', header: t('date'), render: (u) => formatDateTime(u.created_at) },
    {
      key: 'actions', header: t('actions'),
      render: (u) => (
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" className="text-error" onClick={() => { if (confirm(t('confirmDelete'))) deleteMutation.mutate(u.id); }}>
            {t('delete')}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">{t('users')}</h1>
          <p className="text-on-surface-variant mt-1">{t('total')}: {data?.total ?? 0}</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          {t('addUser', 'إضافة مستخدم')}
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items || []}
        keyExtractor={(u) => u.id}
        isLoading={isLoading}
        searchable
        searchKeys={['name', 'email']}
        emptyTitle={t('noData')}
      />

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title={t('addUser', 'إضافة مستخدم')}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }} className="space-y-4">
          <Input label={t('fullName')} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <Input label={t('email')} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <Input label={t('password')} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <Select label={t('role')} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })} options={ROLE_OPTIONS} />
          <div className="flex gap-4 justify-end pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>{t('cancel')}</Button>
            <Button type="submit" isLoading={createMutation.isPending}>{t('create')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
