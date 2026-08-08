import { cn } from '@gula/ui-platform';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TrendIndicatorProps {
  value: number;
  direction?: 'up' | 'down' | 'stable';
  showIcon?: boolean;
  showValue?: boolean;
  className?: string;
}

export function TrendIndicator({ value, direction, showIcon = true, showValue = true, className }: TrendIndicatorProps) {
  const dir = direction || (value > 0 ? 'up' : value < 0 ? 'down' : 'stable');
  const absValue = Math.abs(value);

  return (
    <span className={cn(
      'inline-flex items-center gap-1 text-xs font-bold',
      dir === 'up' && 'text-emerald-400',
      dir === 'down' && 'text-rose-400',
      dir === 'stable' && 'text-slate-400',
      className,
    )}>
      {showIcon && (
        dir === 'up' ? <TrendingUp size={14} /> :
        dir === 'down' ? <TrendingDown size={14} /> :
        <Minus size={14} />
      )}
      {showValue && <span>{absValue}%</span>}
    </span>
  );
}
