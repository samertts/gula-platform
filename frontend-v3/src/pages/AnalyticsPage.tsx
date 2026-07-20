import { useQuery } from '@tanstack/react-query';
import { stats } from '@/api/endpoints';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { useTranslation } from 'react-i18next';
import { formatNumber } from '@/lib/utils';
import { BarChart3, TrendingUp, Activity, Clock, BarChart } from 'lucide-react';
import { BarChart as RechartsBar, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function AnalyticsPage() {
  const { t } = useTranslation();

  const { data: summary } = useQuery({ queryKey: ['stats-summary'], queryFn: () => stats.summary().catch(() => null) });
  const { data: daily } = useQuery({ queryKey: ['stats-daily'], queryFn: () => stats.daily(14).catch(() => []) });
  const { data: topTests } = useQuery({ queryKey: ['stats-tests'], queryFn: () => stats.tests(10).catch(() => []) });
  const { data: flags } = useQuery({ queryKey: ['stats-flags'], queryFn: () => stats.flags().catch(() => []) });
  const { data: patientGrowth } = useQuery({ queryKey: ['stats-patients'], queryFn: () => stats.patients(12).catch(() => []) });
  const { data: turnaround } = useQuery({ queryKey: ['stats-turnaround'], queryFn: () => stats.turnaround().catch(() => []) });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-on-surface">{t('analytics')}</h1>
        <p className="text-on-surface-variant mt-1">{t('summary')}</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: t('totalOrders'), value: summary?.total_orders, icon: BarChart3 },
          { label: t('totalPatients'), value: summary?.total_patients, icon: TrendingUp },
          { label: t('totalResults'), value: summary?.total_results, icon: Activity },
          { label: t('turnaroundTime'), value: summary?.avg_turnaround_hours ? `${summary.avg_turnaround_hours}h` : '—', icon: Clock },
        ].map((card) => (
          <div key={card.label} className="rounded-xl border border-outline bg-surface p-5">
            <div className="flex items-center gap-2 mb-2">
              <card.icon className="h-4 w-4 text-on-surface-variant" />
              <p className="text-sm text-on-surface-variant">{card.label}</p>
            </div>
            <p className="text-2xl font-bold text-on-surface">{card.value != null ? formatNumber(card.value) : '—'}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-outline bg-surface p-5">
          <h3 className="font-semibold text-on-surface mb-4">{t('dailyTrend')}</h3>
          {daily && daily.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="orders" stroke="#4f46e5" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="results" stroke="#10b981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <Skeleton className="h-[250px]" />}
        </div>

        <div className="rounded-xl border border-outline bg-surface p-5">
          <h3 className="font-semibold text-on-surface mb-4">{t('testDistribution')}</h3>
          {topTests && topTests.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <RechartsBar data={topTests}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="test_name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </RechartsBar>
            </ResponsiveContainer>
          ) : <Skeleton className="h-[250px]" />}
        </div>

        <div className="rounded-xl border border-outline bg-surface p-5">
          <h3 className="font-semibold text-on-surface mb-4">{t('resultFlags')}</h3>
          {flags && flags.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={flags} dataKey="count" nameKey="flag" cx="50%" cy="50%" outerRadius={80} label>
                  {flags.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <Skeleton className="h-[250px]" />}
        </div>

        <div className="rounded-xl border border-outline bg-surface p-5">
          <h3 className="font-semibold text-on-surface mb-4">{t('patientGrowth')}</h3>
          {patientGrowth && patientGrowth.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={patientGrowth}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <Skeleton className="h-[250px]" />}
        </div>
      </div>

      {turnaround && turnaround.length > 0 && (
        <div className="rounded-xl border border-outline bg-surface p-5">
          <h3 className="font-semibold text-on-surface mb-4">{t('turnaroundTime')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RechartsBar data={turnaround} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="test_name" type="category" tick={{ fontSize: 10 }} width={150} />
              <Tooltip />
              <Bar dataKey="avg_minutes" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </RechartsBar>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
