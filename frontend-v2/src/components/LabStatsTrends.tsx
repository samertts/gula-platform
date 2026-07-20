/**
 * LabStatsTrends — Statistical Trends Dashboard Component
 *
 * Displays time-series analytics from the /stats/* endpoints:
 *  - Daily orders & tests chart
 *  - Top test frequency
 *  - Flag distribution (normal / H / L / critical)
 *  - Summary counters with period comparisons
 *
 * Uses the same design language as LabDashboard.tsx.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp, TrendingDown, AlertCircle, Activity,
  BarChart3, PieChart, Calendar, Clock, RefreshCw,
  FlaskConical, Users,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn, formatNumber, formatTime } from '../lib/utils';
import { useLanguage } from '../contexts/LanguageContext';
import { auth } from '../firebase-auth';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DailySeries {
  date: string;
  orders: number;
  tests: number;
  critical_tests: number;
  abnormal_tests: number;
}

interface TestFreqItem {
  test_name: string;
  count: number;
  critical_count: number;
  abnormal_count: number;
  abnormal_rate: number;
  avg_value: number | null;
}

interface FlagDistribution {
  [flag: string]: { count: number; percentage: number };
}

interface StatsSummary {
  totals: {
    patients: number;
    orders: number;
    tests: number;
    critical_results: number;
    critical_rate_pct: number;
  };
  today: { orders: number; critical_results: number };
  this_week: { orders: number };
  this_month: { orders: number };
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function useApiToken(): string | null {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    auth.currentUser?.getIdToken().then(setToken).catch(() => {});
  }, []);
  return token;
}

async function fetchStats<T>(endpoint: string, token: string | null): Promise<T | null> {
  if (!token) return null;
  try {
    const base = import.meta.env.VITE_API_URL || '';
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) return null;
    return resp.json();
  } catch {
    return null;
  }
}

// ─── Mini bar-chart (pure CSS / motion) ──────────────────────────────────────

const MiniBarChart: React.FC<{ data: { label: string; value: number; color: string }[] }> = ({ data }) => {
  const max = Math.max(...data.map(d => d.value), 1);
  return (
    <div className="flex items-end gap-1 h-16">
      {data.map((d, i) => (
        <motion.div
          key={i}
          title={`${d.label}: ${d.value}`}
          className={cn('flex-1 rounded-t-sm opacity-80 hover:opacity-100 cursor-default', d.color)}
          initial={{ height: 0 }}
          animate={{ height: `${Math.max((d.value / max) * 64, 2)}px` }}
          transition={{ delay: i * 0.03, type: 'spring', stiffness: 120 }}
        />
      ))}
    </div>
  );
};

// ─── Flag pill ────────────────────────────────────────────────────────────────

const FLAG_COLORS: Record<string, string> = {
  normal: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  H: 'bg-orange-50 text-orange-700 border-orange-200',
  L: 'bg-sky-50 text-sky-700 border-sky-200',
  critical: 'bg-red-50 text-red-700 border-red-200',
  unknown: 'bg-slate-50 text-slate-500 border-slate-200',
};

const FLAG_LABELS: Record<string, string> = {
  normal: 'طبيعي',
  H: 'مرتفع',
  L: 'منخفض',
  critical: 'خطير',
  unknown: 'غير معروف',
};

// ─── Section card ─────────────────────────────────────────────────────────────

const SectionCard: React.FC<{
  title: string;
  titleAr: string;
  icon: React.ComponentType<any>;
  children: React.ReactNode;
  className?: string;
}> = ({ title, titleAr, icon: Icon, children, className }) => {
  const { language } = useLanguage();
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'bg-white/60 backdrop-blur-md rounded-3xl border border-white shadow-sm p-6',
        className,
      )}
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2.5 bg-slate-900 rounded-xl text-white">
          <Icon size={18} />
        </div>
        <h3 className="font-black text-slate-800 text-sm tracking-tight">
          {language === 'AR' ? titleAr : title}
        </h3>
      </div>
      {children}
    </motion.div>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────

interface LabStatsTrendsProps {
  className?: string;
}

const LabStatsTrends: React.FC<LabStatsTrendsProps> = ({ className }) => {
  const { language } = useLanguage();
  const token = useApiToken();

  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [daily, setDaily] = useState<DailySeries[]>([]);
  const [topTests, setTopTests] = useState<TestFreqItem[]>([]);
  const [flags, setFlags] = useState<FlagDistribution>({});

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [sumData, dailyData, testData, flagData] = await Promise.all([
        fetchStats<StatsSummary>('/stats/summary', token),
        fetchStats<{ series: DailySeries[] }>(`/stats/trends/daily?days=${days}`, token),
        fetchStats<{ top_tests: TestFreqItem[] }>(`/stats/trends/tests?days=${days}&limit=8`, token),
        fetchStats<{ distribution: FlagDistribution }>(`/stats/trends/flags?days=${days}`, token),
      ]);
      if (sumData) setSummary(sumData);
      if (dailyData) setDaily(dailyData.series);
      if (testData) setTopTests(testData.top_tests);
      if (flagData) setFlags(flagData.distribution);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }, [token, days]);

  useEffect(() => { load(); }, [load]);

  const isAr = language === 'AR';

  // ── Summary counters ───────────────────────────────────────────────────────
  const summaryCards = summary
    ? [
        {
          label: isAr ? 'إجمالي المرضى' : 'Total Patients',
          value: formatNumber(summary.totals.patients, language),
          icon: Users,
          color: 'bg-violet-600',
          sub: isAr ? `${formatNumber(summary.today.orders, language)} طلب اليوم` : `${formatNumber(summary.today.orders, language)} orders today`,
        },
        {
          label: isAr ? 'إجمالي الطلبات' : 'Total Orders',
          value: formatNumber(summary.totals.orders, language),
          icon: FlaskConical,
          color: 'bg-indigo-600',
          sub: isAr ? `هذا الشهر: ${formatNumber(summary.this_month.orders, language)}` : `This month: ${formatNumber(summary.this_month.orders, language)}`,
        },
        {
          label: isAr ? 'إجمالي الفحوصات' : 'Total Tests',
          value: formatNumber(summary.totals.tests, language),
          icon: Activity,
          color: 'bg-sky-600',
          sub: isAr ? 'منذ البداية' : 'All time',
        },
        {
          label: isAr ? 'نتائج خطيرة' : 'Critical Results',
          value: formatNumber(summary.totals.critical_results, language),
          icon: AlertCircle,
          color: 'bg-red-600',
          sub: `${summary.totals.critical_rate_pct}%`,
        },
      ]
    : [];

  // ── Daily chart data ───────────────────────────────────────────────────────
  const dailyChartData = daily.slice(-14).map(d => ({
    label: d.date,
    value: d.orders,
    color: 'bg-indigo-400',
  }));
  const criticalChartData = daily.slice(-14).map(d => ({
    label: d.date,
    value: d.critical_tests,
    color: 'bg-red-400',
  }));

  return (
    <div className={cn('space-y-6', className)}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">
            {isAr ? 'الإحصائيات والاتجاهات' : 'Statistics & Trends'}
          </h2>
          {lastUpdated && (
            <p className="text-[11px] text-slate-400 mt-0.5">
              {isAr ? 'آخر تحديث: ' : 'Last updated: '}
              {formatTime(lastUpdated, language)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Days selector */}
          <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
            {[7, 14, 30, 90].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-xs font-bold transition-all',
                  days === d
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-900',
                )}
              >
                {d}{isAr ? 'ي' : 'd'}
              </button>
            ))}
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="p-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={cn('transition-transform', loading && 'animate-spin')} />
          </button>
        </div>
      </div>

      {/* ── Summary cards ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((card, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="bg-white/60 backdrop-blur-md rounded-2xl border border-white shadow-sm p-5"
          >
            <div className={cn('inline-flex p-2.5 rounded-xl text-white mb-3', card.color)}>
              <card.icon size={18} />
            </div>
            <div className="text-3xl font-black text-slate-900 tracking-tighter mb-1">
              {card.value}
            </div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              {card.label}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">{card.sub}</div>
          </motion.div>
        ))}
      </div>

      {/* ── Charts row ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily orders mini-chart */}
        <SectionCard
          title="Daily Orders"
          titleAr="الطلبات اليومية"
          icon={BarChart3}
        >
          {daily.length > 0 ? (
            <>
              <MiniBarChart data={dailyChartData} />
              <div className="flex justify-between text-[10px] text-slate-400 mt-2">
                <span>{daily[0]?.date}</span>
                <span>{daily[daily.length - 1]?.date}</span>
              </div>
            </>
          ) : (
            <div className="h-16 flex items-center justify-center text-slate-400 text-sm">
              {isAr ? 'لا توجد بيانات' : 'No data'}
            </div>
          )}
        </SectionCard>

        {/* Critical results mini-chart */}
        <SectionCard
          title="Critical Results / Day"
          titleAr="النتائج الخطيرة يومياً"
          icon={AlertCircle}
        >
          {daily.length > 0 ? (
            <>
              <MiniBarChart data={criticalChartData} />
              <div className="flex justify-between text-[10px] text-slate-400 mt-2">
                <span>{daily[0]?.date}</span>
                <span>{daily[daily.length - 1]?.date}</span>
              </div>
            </>
          ) : (
            <div className="h-16 flex items-center justify-center text-slate-400 text-sm">
              {isAr ? 'لا توجد بيانات' : 'No data'}
            </div>
          )}
        </SectionCard>
      </div>

      {/* ── Top tests + Flag distribution ───────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top tests */}
        <SectionCard
          title="Top Tests"
          titleAr="أكثر الفحوصات طلباً"
          icon={FlaskConical}
        >
          <div className="space-y-2">
            {topTests.length === 0 && (
              <p className="text-slate-400 text-sm text-center py-4">
                {isAr ? 'لا توجد بيانات' : 'No data'}
              </p>
            )}
            {topTests.map((t, i) => {
              const barPct = topTests[0] ? (t.count / topTests[0].count) * 100 : 0;
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-[11px] font-bold text-slate-400 w-4 text-right">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-xs font-bold text-slate-700 truncate">{t.test_name}</span>
                      <span className="text-xs text-slate-400 ml-2 shrink-0">{formatNumber(t.count, language)}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <motion.div
                        className={cn(
                          'h-full rounded-full',
                          t.abnormal_rate > 20 ? 'bg-orange-400' : 'bg-indigo-400',
                        )}
                        initial={{ width: 0 }}
                        animate={{ width: `${barPct}%` }}
                        transition={{ delay: i * 0.04 }}
                      />
                    </div>
                  </div>
                  {t.abnormal_rate > 0 && (
                    <span className={cn(
                      'text-[10px] font-bold shrink-0 px-1.5 py-0.5 rounded-full',
                      t.abnormal_rate > 20
                        ? 'bg-orange-50 text-orange-600'
                        : 'bg-slate-50 text-slate-500',
                    )}>
                      {t.abnormal_rate}%
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </SectionCard>

        {/* Flag distribution */}
        <SectionCard
          title="Result Flag Distribution"
          titleAr="توزيع نتائج الفحوصات"
          icon={PieChart}
        >
          <div className="space-y-2.5">
            {Object.keys(flags).length === 0 && (
              <p className="text-slate-400 text-sm text-center py-4">
                {isAr ? 'لا توجد بيانات' : 'No data'}
              </p>
            )}
            {Object.entries(flags)
              .sort(([, a], [, b]) => b.count - a.count)
              .map(([flag, info]) => (
                <div key={flag} className="flex items-center gap-3">
                  <span className={cn(
                    'text-[10px] font-black px-2 py-0.5 rounded-full border w-16 text-center shrink-0',
                    FLAG_COLORS[flag] ?? FLAG_COLORS.unknown,
                  )}>
                    {isAr ? (FLAG_LABELS[flag] ?? flag) : flag}
                  </span>
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <motion.div
                      className={cn(
                        'h-full rounded-full',
                        flag === 'critical' ? 'bg-red-400'
                          : flag === 'H' ? 'bg-orange-400'
                          : flag === 'L' ? 'bg-sky-400'
                          : 'bg-emerald-400',
                      )}
                      initial={{ width: 0 }}
                      animate={{ width: `${info.percentage}%` }}
                      transition={{ type: 'spring', stiffness: 80 }}
                    />
                  </div>
                  <span className="text-xs font-bold text-slate-500 w-10 text-right shrink-0">
                    {info.percentage}%
                  </span>
                </div>
              ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
};

export default LabStatsTrends;
