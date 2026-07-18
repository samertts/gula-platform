import { useState, useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { cn } from '@gula/ui-platform';
import type { VitalSigns } from '@/utils/types';

interface VitalSignsChartProps {
  data: VitalSigns[];
  metrics?: ('temperature' | 'heartRate' | 'respiratoryRate' | 'bloodPressure' | 'oxygenSaturation')[];
  className?: string;
}

const metricConfig: Record<string, { label: string; color: string; unit: string; key: string }> = {
  temperature: { label: 'درجة الحرارة', color: '#ef4444', unit: '°C', key: 'temperature' },
  heartRate: { label: 'معدل القلب', color: '#ec4899', unit: '/دقيقة', key: 'heartRate' },
  respiratoryRate: { label: 'التنفس', color: '#8b5cf6', unit: '/دقيقة', key: 'respiratoryRate' },
  bloodPressure: { label: 'ضغط الدم', color: '#f97316', unit: 'mmHg', key: 'bloodPressureSystolic' },
  oxygenSaturation: { label: 'تشبع O2', color: '#06b6d4', unit: '%', key: 'oxygenSaturation' },
};

export function VitalSignsChart({ data, metrics = ['temperature', 'heartRate', 'respiratoryRate', 'oxygenSaturation'], className }: VitalSignsChartProps) {
  const [selectedMetric, setSelectedMetric] = useState(metrics[0]);

  const chartData = useMemo(() => {
    return [...data]
      .sort((a, b) => new Date(a.recordedAt).getTime() - new Date(b.recordedAt).getTime())
      .map(d => ({
        time: new Date(d.recordedAt).toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
        temperature: d.temperature,
        heartRate: d.heartRate,
        respiratoryRate: d.respiratoryRate,
        systolic: d.bloodPressureSystolic,
        diastolic: d.bloodPressureDiastolic,
        oxygenSaturation: d.oxygenSaturation,
        painScore: d.painScore,
      }));
  }, [data]);

  const config = metricConfig[selectedMetric];
  if (!config) return null;

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex gap-2 flex-wrap">
        {metrics.map(m => {
          const cfg = metricConfig[m];
          return (
            <button
              key={m}
              type="button"
              onClick={() => setSelectedMetric(m)}
              className={cn(
                'px-3 py-1.5 text-xs font-bold rounded-xl transition-colors',
                selectedMetric === m
                  ? 'bg-primary-500 text-white'
                  : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-600',
              )}
            >
              {cfg.label}
            </button>
          );
        })}
      </div>

      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              axisLine={{ stroke: '#334155' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              axisLine={{ stroke: '#334155' }}
              tickLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '12px',
                color: '#f1f5f9',
                fontSize: '12px',
              }}
              labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
            />
            <Legend
              formatter={(value: string) => <span className="text-xs text-neutral-400">{value}</span>}
            />
            {selectedMetric === 'bloodPressure' ? (
              <>
                <Line type="monotone" dataKey="systolic" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} name="الانقباضي" />
                <Line type="monotone" dataKey="diastolic" stroke="#fbbf24" strokeWidth={2} dot={{ r: 3 }} name="الانبساطي" />
              </>
            ) : (
              <Line
                type="monotone"
                dataKey={config.key}
                stroke={config.color}
                strokeWidth={2}
                dot={{ r: 3, fill: config.color }}
                name={config.label}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {data.length > 0 && (() => {
          const latest = data[data.length - 1];
          const items = [
            { label: 'درجة الحرارة', value: latest.temperature !== null ? `${latest.temperature}°C` : '--' },
            { label: 'معدل القلب', value: latest.heartRate !== null ? `${latest.heartRate} /د` : '--' },
            { label: 'التنفس', value: latest.respiratoryRate !== null ? `${latest.respiratoryRate} /د` : '--' },
            { label: 'تشبع O2', value: latest.oxygenSaturation !== null ? `${latest.oxygenSaturation}%` : '--' },
          ];
          return items.map(item => (
            <div key={item.label} className="bg-neutral-50 dark:bg-neutral-700/50 p-2 rounded-xl text-center">
              <p className="text-[10px] text-neutral-400 dark:text-neutral-500">{item.label}</p>
              <p className="text-sm font-bold text-neutral-800 dark:text-neutral-200">{item.value}</p>
            </div>
          ));
        })()}
      </div>
    </div>
  );
}
