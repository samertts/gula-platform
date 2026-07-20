import { useQuery } from '@tanstack/react-query';
import { dashboard, stats, criticalAlerts } from '@/api/endpoints';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { StatusBadge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { formatNumber, formatDateTime } from '@/lib/utils';
import {
  Activity, FlaskConical, Users, AlertTriangle, Clock,
  TrendingUp, BarChart3,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  const { data: ds, isLoading: dsLoading, error: dsError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboard.stats().catch(() => null),
  });

  const { data: sm } = useQuery({
    queryKey: ['stats-summary'],
    queryFn: () => stats.summary().catch(() => null),
  });

  const { data: alerts } = useQuery({
    queryKey: ['critical-alerts'],
    queryFn: () => criticalAlerts.list({ hours: 24 }).catch(() => []),
  });

  const statCards = [
    { label: t('ordersToday'), value: ds?.orders_today ?? sm?.today_orders, icon: Activity, color: 'text-blue-600 bg-blue-50' },
    { label: t('resultsToday'), value: ds?.results_today ?? sm?.today_results, icon: FlaskConical, color: 'text-emerald-600 bg-emerald-50' },
    { label: t('newPatients'), value: ds?.patients_today ?? sm?.today_patients, icon: Users, color: 'text-violet-600 bg-violet-50' },
    { label: t('pending'), value: ds?.pending_orders, icon: Clock, color: 'text-amber-600 bg-amber-50' },
    { label: t('totalOrders'), value: sm?.total_orders, icon: TrendingUp, color: 'text-indigo-600 bg-indigo-50' },
    { label: t('totalPatients'), value: sm?.total_patients, icon: BarChart3, color: 'text-rose-600 bg-rose-50' },
  ];

  if (dsLoading) return <CardSkeleton count={6} />;

  if (dsError && !ds && !sm) {
    return (
      <EmptyState
        icon={Activity}
        title={t('error')}
        description={t('noData')}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-on-surface">{t('dashboard')}</h1>
        <p className="text-on-surface-variant mt-1">{t('greeting')}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className="rounded-xl border border-outline bg-surface p-5 space-y-3">
            <div className={`inline-flex p-2 rounded-lg ${card.color}`}>
              <card.icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-on-surface">
                {card.value != null ? formatNumber(card.value) : '—'}
              </p>
              <p className="text-sm text-on-surface-variant">{card.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-outline bg-surface">
          <div className="flex items-center justify-between px-5 py-4 border-b border-outline">
            <h3 className="font-semibold text-on-surface">
              <AlertTriangle className="h-4 w-4 inline mr-2 text-error" />
              {t('criticalAlerts', 'التنبيهات الحرجة')}
            </h3>
            <Link to="/alerts" className="text-sm text-primary hover:underline">{t('viewAll')}</Link>
          </div>
          <div className="p-4">
            {!alerts || alerts.length === 0 ? (
              <p className="text-sm text-on-surface-variant text-center py-8">{t('noData')}</p>
            ) : (
              <div className="space-y-2">
                {alerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low">
                    <div>
                      <p className="text-sm font-medium text-on-surface">{alert.test_name}</p>
                      <p className="text-xs text-on-surface-variant">{formatDateTime(alert.created_at)}</p>
                    </div>
                    <StatusBadge status={alert.flag} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-outline bg-surface">
          <div className="flex items-center justify-between px-5 py-4 border-b border-outline">
            <h3 className="font-semibold text-on-surface">
              <Activity className="h-4 w-4 inline mr-2 text-primary" />
              {t('recentActivity', 'النشاط الأخير')}
            </h3>
          </div>
          <div className="p-4">
            {!ds?.recent_activity || ds.recent_activity.length === 0 ? (
              <p className="text-sm text-on-surface-variant text-center py-8">{t('noData')}</p>
            ) : (
              <div className="space-y-2">
                {ds.recent_activity.map((log) => (
                  <div key={log.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low">
                    <div>
                      <p className="text-sm text-on-surface">{log.action} — {log.resource_type}</p>
                      <p className="text-xs text-on-surface-variant">{formatDateTime(log.created_at)}</p>
                    </div>
                    <StatusBadge status={log.action} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
