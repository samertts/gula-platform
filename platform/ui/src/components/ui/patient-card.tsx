import * as React from 'react';
import { cn } from '../../lib/utils';
import { Badge } from './badge';

interface PatientCardProps {
  name: string;
  nationalId?: string;
  age?: number;
  gender?: string;
  patientId: string;
  labId?: string;
  className?: string;
  onClick?: () => void;
}

export function PatientCard({
  name,
  nationalId,
  age,
  gender,
  patientId,
  labId,
  className,
  onClick,
}: PatientCardProps) {
  return (
    <div
      className={cn(
        'flex cursor-pointer items-center gap-4 rounded-xl border border-surface-200 bg-white p-4 shadow-sm transition-all hover:border-primary-300 hover:shadow-md',
        'dark:border-dark-surface-200 dark:bg-dark-surface-100 dark:hover:border-primary-600',
        className,
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
      aria-label={`Patient: ${name}`}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300">
        <span className="text-lg font-bold">{name.charAt(0)}</span>
      </div>
      <div className="flex flex-1 flex-col gap-1">
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold text-surface-900 dark:text-dark-surface-900">
            {name}
          </h3>
          {gender && (
            <span className="text-xs text-surface-500">{gender}</span>
          )}
          {age && (
            <span className="text-xs text-surface-500">{age} years</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm text-surface-500">
          <span>ID: {patientId}</span>
          {nationalId && <span>National ID: {nationalId}</span>}
        </div>
        {labId && (
          <Badge variant="default" className="w-fit">
            Lab: {labId}
          </Badge>
        )}
      </div>
    </div>
  );
}
