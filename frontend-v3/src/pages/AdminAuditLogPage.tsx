import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { admin } from '@/api/endpoints';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { useTranslation } from 'react-i18next';
import { formatDateTime, paginationParams } from '@/lib/utils';
import type { AuditLog } from '@/types/backend';

export function AdminAuditLogPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ['admin-audit-log', page],
    queryFn: () => admin.auditLog(paginationParams(page * 20, 20)),
  });

  const columns: Column<AuditLog>[] = [
    { key: 'action', header: t('action', 'الإجراء'), sortable: true, render: (l) => <StatusBadge status={l.action} /> },
    { key: 'resource_type', header: t('resource', 'الموارد') },
    { key: 'resource_id', header: 'ID' },
    { key: 'user_role', header: t('role') },
    { key: 'ip_address', header: 'IP' },
    { key: 'created_at', header: t('date'), sortable: true, render: (l) => formatDateTime(l.created_at) },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-on-surface">{t('auditLog')}</h1>
        <p className="text-on-surface-variant mt-1">{t('total')}: {data?.total ?? 0}</p>
      </div>
      <DataTable
        columns={columns}
        data={data?.items || []}
        keyExtractor={(l) => l.id}
        isLoading={isLoading}
        emptyTitle={t('noData')}
      />
    </div>
  );
}
