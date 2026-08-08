import { useMemo } from 'react';
import { cn } from '@gula/ui-platform';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
} from 'recharts';
import type { QCData } from '@/utils/types';

interface QCChartProps {
  data: QCData;
  width?: number | string;
  height?: number;
  className?: string;
}

export function QCChart({ data, height = 280, className }: QCChartProps) {
  const { mean, sd, history, status } = data;

  const chartData = useMemo(() => {
    return history.map(p => ({
      ...p,
      mean,
      plus1sd: mean + sd,
      minus1sd: mean - sd,
      plus2sd: mean + 2 * sd,
      minus2sd: mean - 2 * sd,
      plus3sd: mean + 3 * sd,
      minus3sd: mean - 3 * sd,
    }));
  }, [history, mean, sd]);

  const yDomain = useMemo(() => {
    const min = Math.min(mean - 4 * sd, ...history.map(p => p.value));
    const max = Math.max(mean + 4 * sd, ...history.map(p => p.value));
    return [min - sd * 0.5, max + sd * 0.5] as [number, number];
  }, [mean, sd, history]);

  const statusColor = status === 'in_control' ? '#22c55e' : status === 'warning' ? '#f59e0b' : '#ef4444';

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
            {data.testName} - المستوى {data.level}
          </span>
          <span className={cn(
            'px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider',
            status === 'in_control' && 'bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400',
            status === 'warning' && 'bg-warning-50 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400',
            status === 'out_of_control' && 'bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400',
            status === 'not_run' && 'bg-neutral-100 text-neutral-500 dark:bg-neutral-700 dark:text-neutral-400',
          )}>
            {status === 'in_control' ? 'تحت السيطرة' : status === 'warning' ? 'تحذير' : status === 'out_of_control' ? 'خارج السيطرة' : 'لم يتم'}
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs font-medium text-neutral-500 dark:text-neutral-400">
          <span>المتوسط: {mean.toFixed(2)}</span>
          <span>SD: {sd.toFixed(2)}</span>
          <span>CV: {((sd / mean) * 100).toFixed(2)}%</span>
        </div>
      </div>

      <div className="rounded-2xl bg-white dark:bg-neutral-800 p-4 border border-neutral-200 dark:border-neutral-700">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 20, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-neutral-700" />

            <ReferenceArea y1={mean + 2 * sd} y2={mean + 3 * sd} fill="#fef3c7" fillOpacity={0.3} />
            <ReferenceArea y1={mean - 3 * sd} y2={mean - 2 * sd} fill="#fef3c7" fillOpacity={0.3} />
            <ReferenceArea y1={mean + 3 * sd} y2={yDomain[1]} fill="#fee2e2" fillOpacity={0.2} />
            <ReferenceArea y1={yDomain[0]} y2={mean - 3 * sd} fill="#fee2e2" fillOpacity={0.2} />

            <ReferenceLine y={mean} stroke="#64748b" strokeWidth={2} label={{ value: 'Mean', position: 'right', fill: '#64748b', fontSize: 11 }} />
            <ReferenceLine y={mean + sd} stroke="#94a3b8" strokeDasharray="4 4" strokeWidth={1} />
            <ReferenceLine y={mean - sd} stroke="#94a3b8" strokeDasharray="4 4" strokeWidth={1} />
            <ReferenceLine y={mean + 2 * sd} stroke="#f59e0b" strokeDasharray="4 4" strokeWidth={1.5} />
            <ReferenceLine y={mean - 2 * sd} stroke="#f59e0b" strokeDasharray="4 4" strokeWidth={1.5} />
            <ReferenceLine y={mean + 3 * sd} stroke="#ef4444" strokeDasharray="4 4" strokeWidth={1.5} />
            <ReferenceLine y={mean - 3 * sd} stroke="#ef4444" strokeDasharray="4 4" strokeWidth={1.5} />

            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => {
                const d = new Date(v);
                return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
              }}
            />
            <YAxis
              domain={yDomain}
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => v.toFixed(1)}
            />
            <Tooltip
              contentStyle={{
                borderRadius: '12px',
                border: 'none',
                boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)',
                fontWeight: 600,
                fontSize: '12px',
              }}
              cursor={{ stroke: statusColor, strokeWidth: 2 }}
            />

            <Line
              type="monotone"
              dataKey="value"
              stroke={statusColor}
              strokeWidth={2.5}
              dot={{ r: 4, fill: statusColor, strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 6, fill: statusColor, strokeWidth: 2, stroke: '#fff' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {data.westgardViolations && data.westgardViolations.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.westgardViolations.map(violation => (
            <span
              key={violation}
              className="px-2.5 py-1 bg-danger-50 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400 rounded-full text-[10px] font-black uppercase tracking-wider"
            >
              {violation}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
