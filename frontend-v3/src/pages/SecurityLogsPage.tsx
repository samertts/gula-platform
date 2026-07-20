import { useQuery } from '@tanstack/react-query';
import { security, admin } from '@/api/endpoints';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/Badge';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { useTranslation } from 'react-i18next';
import { formatNumber, formatDateTime } from '@/lib/utils';
import type { AuditLog } from '@/types/backend';
import { ShieldAlert, Activity, Users, AlertTriangle } from 'lucide-react';

export function SecurityLogsPage() {
  const { t } = useTranslation();

  const { data: secStatus, isLoading: secLoading } = useQuery({
    queryKey: ['security-status'],
    queryFn: () => security.status().catch(() => null),
  });

  const { data: auditData } = useQuery({
    queryKey: ['audit-log-recent'],
    queryFn: () => admin.auditLog({ skip: 0, limit: 50 }),
  });

  const columns: Column<AuditLog>[] = [
    { key: 'action', header: t('action', 'الإجراء'), render: (l) => <StatusBadge status={l.action} /> },
    { key: 'resource_type', header: t('resource', 'الموارد') },
    { key: 'user_role', header: t('role') },
    { key: 'ip_address', header: 'IP' },
    { key: 'created_at', header: t('date'), render: (l) => formatDateTime(l.created_at) },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-on-surface flex items-center gap-2">
          <ShieldAlert className="h-6 w-6" />
          {t('securityLogs')}
        </h1>
      </div>

      {secStatus ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-xl border border-outline bg-surface p-5">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="h-4 w-4 text-on-surface-variant" />
              <p className="text-sm text-on-surface-variant">{t('recentLogins', 'آخر تسجيلات الدخول')}</p>
            </div>
            <p className="text-2xl font-bold text-on-surface">{formatNumber(secStatus.recent_logins)}</p>
          </div>
          <div className="rounded-xl border border-outline bg-surface p-5">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-on-surface-variant" />
              <p className="text-sm text-on-surface-variant">{t('failedAttempts', 'محاولات فاشلة')}</p>
            </div>
            <p className="text-2xl font-bold text-on-surface">{formatNumber(secStatus.failed_attempts)}</p>
          </div>
          <div className="rounded-xl border border-outline bg-surface p-5">
            <div className="flex items-center gap-2 mb-2">
              <ShieldAlert className="h-4 w-4 text-on-surface-variant" />
              <p className="text-sm text-on-surface-variant">{t('mfa')}</p>
            </div>
            <p className="text-2xl font-bold text-on-surface">{secStatus.mfa_enabled ? t('active') : t('inactive')}</p>
          </div>
          <div className="rounded-xl border border-outline bg-surface p-5">
            <div className="flex items-center gap-2 mb-2">
              <Users className="h-4 w-4 text-on-surface-variant" />
              <p className="text-sm text-on-surface-variant">{t('activeSessions')}</p>
            </div>
            <p className="text-2xl font-bold text-on-surface">{formatNumber(secStatus.active_sessions)}</p>
          </div>
        </div>
      ) : secLoading ? <CardSkeleton count={4} /> : null}

      <div className="rounded-xl border border-outline bg-surface overflow-hidden">
        <div className="px-6 py-4 border-b border-outline">
          <h3 className="font-semibold text-on-surface">{t('auditLog')}</h3>
        </div>
        <div className="p-4">
          <DataTable
            columns={columns}
            data={auditData?.items || []}
            keyExtractor={(l) => l.id}
            isLoading={!auditData}
            emptyTitle={t('noData')}
          />
        </div>
      </div>
    </div>
  );
}
