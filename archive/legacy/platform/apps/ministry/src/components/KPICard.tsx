import { motion } from 'motion/react';
import { cn } from '@gula/ui-platform';
import { TrendIndicator } from './TrendIndicator';
import type { KpiMetric } from '../services/api';
import { Activity, Users, Building2, Microscope, BedDouble, Syringe, Heart, AlertTriangle } from 'lucide-react';

const iconMap: Record<string, any> = {
  Activity, Users, Building2, Microscope, BedDouble, Syringe, Heart, AlertTriangle,
};

interface KPICardProps {
  metric: KpiMetric;
  onClick?: () => void;
}

export function KPICard({ metric, onClick }: KPICardProps) {
  const Icon = iconMap[metric.icon] || Activity;

  return (
    <motion.div
      whileHover={{ y: -2 }}
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-2xl border p-5 cursor-pointer transition-all',
        'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20',
      )}
    >
      <div className={cn(
        'absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl -mr-12 -mt-12 pointer-events-none',
        metric.color === 'emerald' && 'bg-emerald-500/10',
        metric.color === 'indigo' && 'bg-indigo-500/10',
        metric.color === 'amber' && 'bg-amber-500/10',
        metric.color === 'rose' && 'bg-rose-500/10',
        metric.color === 'violet' && 'bg-violet-500/10',
        metric.color === 'cyan' && 'bg-cyan-500/10',
      )} />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <div className={cn(
            'w-10 h-10 rounded-xl flex items-center justify-center',
            'bg-white/10',
          )}>
            <Icon size={20} className="text-indigo-400" />
          </div>
          <TrendIndicator value={metric.trend} direction={metric.trendUp ? 'up' : 'down'} />
        </div>
        <p className="text-xs text-slate-400 font-medium mb-1">{metric.labelAr}</p>
        <div className="flex items-baseline gap-1.5">
          <span className="text-2xl font-black text-white tracking-tight">
            {metric.value.toLocaleString('ar-IQ')}
          </span>
          <span className="text-xs text-slate-500 font-medium">{metric.unit}</span>
        </div>
      </div>
    </motion.div>
  );
}
