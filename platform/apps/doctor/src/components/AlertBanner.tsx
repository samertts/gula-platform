import { useState } from 'react';
import { cn } from '@gula/ui-platform';

interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  titleAr: string;
  message: string;
  messageAr: string;
  patientId?: string;
  patientName?: string;
  actionable?: boolean;
  onAction?: () => void;
}

interface AlertBannerProps {
  alerts: Alert[];
  onDismiss?: (id: string) => void;
  maxVisible?: number;
}

const typeStyles = {
  critical: {
    bg: 'bg-danger-50 dark:bg-danger-950 border-danger-200 dark:border-danger-900',
    icon: 'text-danger-500',
    title: 'text-danger-800 dark:text-danger-300',
    message: 'text-danger-700 dark:text-danger-400',
    dot: 'bg-danger-500',
  },
  warning: {
    bg: 'bg-warning-50 dark:bg-warning-950 border-warning-200 dark:border-warning-900',
    icon: 'text-warning-500',
    title: 'text-warning-800 dark:text-warning-300',
    message: 'text-warning-700 dark:text-warning-400',
    dot: 'bg-warning-500',
  },
  info: {
    bg: 'bg-info-50 dark:bg-info-950 border-info-200 dark:border-info-900',
    icon: 'text-info-500',
    title: 'text-info-800 dark:text-info-300',
    message: 'text-info-700 dark:text-info-400',
    dot: 'bg-info-500',
  },
};

export function AlertBanner({ alerts, onDismiss, maxVisible = 3 }: AlertBannerProps) {
  const [expanded, setExpanded] = useState(false);
  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  const visibleAlerts = expanded ? alerts : alerts.slice(0, maxVisible);

  if (alerts.length === 0) return null;

  return (
    <div className="space-y-2">
      {visibleAlerts.map(alert => {
        const style = typeStyles[alert.type];
        return (
          <div
            key={alert.id}
            className={cn(
              'relative flex items-start gap-3 p-3 rounded-xl border',
              style.bg,
              alert.type === 'critical' && 'animate-[pulse_2s_ease-in-out_infinite]',
            )}
            role="alert"
          >
            <div className={cn('w-2 h-2 rounded-full mt-1.5 shrink-0', style.dot, alert.type === 'critical' && 'animate-ping')} />
            <div className="flex-1 min-w-0">
              <p className={cn('text-sm font-bold', style.title)}>
                {isRtl ? alert.titleAr : alert.title}
              </p>
              <p className={cn('text-xs mt-0.5', style.message)}>
                {isRtl ? alert.messageAr : alert.message}
              </p>
              {alert.actionable && alert.onAction && (
                <button
                  onClick={alert.onAction}
                  className="mt-1 text-xs font-bold underline hover:no-underline"
                >
                  {isRtl ? 'عرض' : 'View'}
                </button>
              )}
            </div>
            {onDismiss && (
              <button
                onClick={() => onDismiss(alert.id)}
                className="shrink-0 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                aria-label={isRtl ? 'إغلاق' : 'Close'}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            )}
          </div>
        );
      })}
      {alerts.length > maxVisible && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm text-primary-600 dark:text-primary-400 font-medium hover:underline"
        >
          {expanded
            ? (isRtl ? 'عرض أقل' : 'Show less')
            : (isRtl ? `عرض ${alerts.length - maxVisible} تنبيهات أخرى` : `Show ${alerts.length - maxVisible} more alerts`)}
        </button>
      )}
    </div>
  );
}
