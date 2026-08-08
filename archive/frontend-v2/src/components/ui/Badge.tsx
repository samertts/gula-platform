import { cn } from '../../lib/utils';

const variants = {
  default: 'bg-slate-100 text-slate-700',
  primary: 'bg-indigo-100 text-indigo-700',
  success: 'bg-emerald-100 text-emerald-700',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-sky-100 text-sky-700',
};

interface BadgeProps {
  children?: React.ReactNode;
  variant?: keyof typeof variants;
  className?: string;
  dot?: boolean;
  pulsing?: boolean;
  count?: number;
}

export function Badge({ children, variant = 'default', className, dot, pulsing, count }: BadgeProps) {
  if (count !== undefined) {
    return (
      <span className={cn(
        'inline-flex items-center justify-center min-w-[18px] h-[18px] px-1.5 rounded-full text-[9px] font-black leading-none',
        variants[variant],
        className,
      )}>
        {count > 99 ? '99+' : count}
      </span>
    );
  }
  if (!children) return null;

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider',
      variants[variant],
      className,
    )}>
      {dot && (
        <span className={cn(
          'w-1.5 h-1.5 rounded-full bg-current',
          pulsing && 'animate-pulse',
        )} />
      )}
      {children}
    </span>
  );
}
