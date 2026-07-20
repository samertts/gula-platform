import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patients } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { formatDate, getAge, paginationParams } from '@/lib/utils';
import type { Patient } from '@/types/backend';
import { Users, Plus, UserPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function PatientsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ full_name: '', phone: '', birth_date: '', gender: '', email: '' });

  const { data, isLoading } = useQuery({
    queryKey: ['patients', page],
    queryFn: () => patients.list(paginationParams(page * 20, 20)),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => patients.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      setShowCreate(false);
      setForm({ full_name: '', phone: '', birth_date: '', gender: '', email: '' });
    },
  });

  const columns: Column<Patient>[] = [
    { key: 'full_name', header: t('fullName'), sortable: true },
    { key: 'phone', header: t('phone'), sortable: true },
    { key: 'health_id', header: 'Health ID' },
    { key: 'gender', header: t('gender') },
    {
      key: 'birth_date', header: t('age'),
      render: (p) => p.birth_date ? String(getAge(p.birth_date)) : '—',
    },
    {
      key: 'id', header: t('actions'),
      render: (p) => (
        <Button size="sm" variant="ghost" onClick={() => navigate(`/patients/${p.id}`)}>
          {t('details', 'عرض')}
        </Button>
      ),
    },
  ];

  if (!user) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">{t('patients')}</h1>
          <p className="text-on-surface-variant mt-1">{t('total')}: {data?.total ?? 0}</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <UserPlus className="h-4 w-4" />
          {t('addPatient')}
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items || []}
        keyExtractor={(p) => p.id}
        isLoading={isLoading}
        searchable
        searchKeys={['full_name', 'phone', 'health_id']}
        emptyTitle={t('noData')}
        emptyDescription={t('noResults')}
        onRowClick={(p) => navigate(`/patients/${p.id}`)}
      />

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title={t('addPatient')}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }} className="space-y-4">
          <Input label={t('fullName')} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          <Input label={t('phone')} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <Input label={t('birthDate')} type="date" value={form.birth_date} onChange={(e) => setForm({ ...form, birth_date: e.target.value })} />
          <Input label={t('email')} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <div className="flex gap-4 justify-end pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>{t('cancel')}</Button>
            <Button type="submit" isLoading={createMutation.isPending}>{t('create')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
