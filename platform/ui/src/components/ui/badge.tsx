import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary-100 text-primary-700',
        normal: 'bg-clinical-green-50 text-clinical-green-700',
        borderline: 'bg-clinical-yellow-50 text-clinical-yellow-700',
        abnormal: 'bg-clinical-red-50 text-clinical-red-700',
        critical: 'bg-critical-50 text-critical-700 animate-pulse',
        pending: 'bg-surface-100 text-surface-600',
        cancelled: 'bg-surface-200 text-surface-500',
        success: 'bg-clinical-green-50 text-clinical-green-700',
        warning: 'bg-clinical-yellow-50 text-clinical-yellow-700',
        error: 'bg-clinical-red-50 text-clinical-red-700',
        info: 'bg-clinical-blue-50 text-clinical-blue-700',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
