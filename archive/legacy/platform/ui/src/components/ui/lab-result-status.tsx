import * as React from 'react';
import { cn } from '../../lib/utils';

export type LabResultStatus = 'normal' | 'borderline' | 'abnormal' | 'critical' | 'pending' | 'cancelled';

interface LabResultStatusProps {
  status: LabResultStatus;
  value?: string;
  unit?: string;
  referenceRange?: string;
  className?: string;
}

const statusConfig: Record<LabResultStatus, { label: string; textColor: string; bgColor: string; dotColor: string }> = {
  normal: {
    label: 'Normal',
    textColor: 'text-status-normal',
    bgColor: 'bg-clinical-green-50 dark:bg-clinical-green-50/10',
    dotColor: 'bg-status-normal',
  },
  borderline: {
    label: 'Borderline',
    textColor: 'text-status-borderline',
    bgColor: 'bg-clinical-yellow-50 dark:bg-clinical-yellow-50/10',
    dotColor: 'bg-status-borderline',
  },
  abnormal: {
    label: 'Abnormal',
    textColor: 'text-status-abnormal',
    bgColor: 'bg-clinical-red-50 dark:bg-clinical-red-50/10',
    dotColor: 'bg-status-abnormal',
  },
  critical: {
    label: 'Critical',
    textColor: 'text-status-critical',
    bgColor: 'bg-critical-50 dark:bg-critical-50/10',
    dotColor: 'bg-status-critical',
  },
  pending: {
    label: 'Pending',
    textColor: 'text-status-pending',
    bgColor: 'bg-surface-50 dark:bg-dark-surface-100',
    dotColor: 'bg-status-pending',
  },
  cancelled: {
    label: 'Cancelled',
    textColor: 'text-status-cancelled',
    bgColor: 'bg-surface-100 dark:bg-dark-surface-200',
    dotColor: 'bg-status-cancelled',
  },
};

export function LabResultStatus({
  status,
  value,
  unit,
  referenceRange,
  className,
}: LabResultStatusProps) {
  const config = statusConfig[status];

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg p-3',
        config.bgColor,
        className,
      )}
      role="status"
      aria-label={`Result status: ${config.label}`}
    >
      <span className={cn('h-2.5 w-2.5 rounded-full', status === 'critical' && 'animate-pulse', config.dotColor)} />
      <div className="flex flex-1 flex-col gap-0.5">
        <div className="flex items-center justify-between">
          <span className={cn('text-sm font-semibold', config.textColor)}>
            {config.label}
          </span>
          {value && (
            <span className="text-sm font-medium text-surface-900 dark:text-dark-surface-900">
              {value} {unit}
            </span>
          )}
        </div>
        {referenceRange && (
          <span className="text-xs text-surface-500">
            Ref: {referenceRange}
          </span>
        )}
      </div>
    </div>
  );
}
