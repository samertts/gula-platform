import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { AlertTriangle, AlertCircle, Info, AlertOctagon, X, CheckCircle2, Bell } from 'lucide-react';
import type { Alert } from '../services/api';
import { getAlertPriorityScore, getAlertsBySeverity } from '../services/alerts';

interface AlertPanelProps {
  alerts: Alert[];
  onAcknowledge?: (id: string) => void;
  onViewAll?: () => void;
  maxDisplay?: number;
}

const severityConfig = {
  critical: { icon: AlertOctagon, color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20', hoverBg: 'hover:bg-rose-500/20' },
  danger: { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', hoverBg: 'hover:bg-amber-500/20' },
  warning: { icon: AlertCircle, color: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/20', hoverBg: 'hover:bg-indigo-500/20' },
  info: { icon: Info, color: 'text-sky-400', bg: 'bg-sky-500/10', border: 'border-sky-500/20', hoverBg: 'hover:bg-sky-500/20' },
};

export function AlertPanel({ alerts, onAcknowledge, onViewAll, maxDisplay = 5 }: AlertPanelProps) {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const sorted = [...alerts]
    .sort((a, b) => getAlertPriorityScore(b) - getAlertPriorityScore(a))
    .filter(a => !dismissed.has(a.id))
    .slice(0, maxDisplay);

  const bySeverity = getAlertsBySeverity(alerts);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        {(['critical', 'danger', 'warning', 'info'] as const).map(sev => (
          <div key={sev} className={cn(
            'p-3 rounded-xl border text-center',
            severityConfig[sev].bg,
            severityConfig[sev].border,
          )}>
            <p className={cn('text-xl font-black', severityConfig[sev].color)}>
              {bySeverity[sev]?.length || 0}
            </p>
            <p className={cn('text-[10px] font-bold uppercase tracking-wider mt-1', severityConfig[sev].color)}>
              {sev === 'critical' ? 'حرج' : sev === 'danger' ? 'خطر' : sev === 'warning' ? 'تحذير' : 'معلومات'}
            </p>
          </div>
        ))}
      </div>

      <div className="space-y-2">
          {sorted.map(alert => {
            const config = severityConfig[alert.severity];
            const Icon = config.icon;
            return (
              <div
                key={alert.id}
                className={cn(
                  'p-4 rounded-xl border transition-all group',
                  config.bg, config.border, config.hoverBg,
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={cn('p-2 rounded-lg shrink-0', config.bg, config.border)}>
                    <Icon size={18} className={config.color} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-bold text-white">{alert.titleAr}</p>
                        <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{alert.descriptionAr}</p>
                      </div>
                      {!alert.acknowledged && onAcknowledge && (
                        <button
                          onClick={() => { onAcknowledge(alert.id); setDismissed(prev => new Set(prev).add(alert.id)); }}
                          className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-slate-400 hover:text-white shrink-0 opacity-0 group-hover:opacity-100 transition-all"
                        >
                          <CheckCircle2 size={16} />
                        </button>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-[10px] text-slate-500 font-medium">{alert.region}</span>
                      <span className="text-[10px] text-slate-600">•</span>
                      <span className="text-[10px] text-slate-500 font-medium">
                        {new Date(alert.createdAt).toLocaleDateString('ar-IQ')}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
      </div>

      {alerts.length > maxDisplay && onViewAll && (
        <button
          onClick={onViewAll}
          className="w-full py-3 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors text-center border border-dashed border-white/10 rounded-xl hover:border-indigo-500/30"
        >
          عرض جميع الإنذارات ({alerts.length})
        </button>
      )}
    </div>
  );
}
