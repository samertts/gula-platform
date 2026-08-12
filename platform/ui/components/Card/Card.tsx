import { type ReactNode, type HTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  variant?: 'default' | 'elevated' | 'outlined' | 'glass';
}

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

const variantStyles = {
  default: 'bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 shadow-sm',
  elevated: 'bg-white dark:bg-neutral-800 shadow-lg shadow-neutral-200/50 dark:shadow-black/20 border border-neutral-100 dark:border-neutral-700',
  outlined: 'bg-transparent border-2 border-neutral-200 dark:border-neutral-700',
  glass: 'bg-white/70 dark:bg-neutral-800/70 backdrop-blur-xl border border-white/40 dark:border-neutral-700/40 shadow-lg',
};

export function Card({
  hover = false,
  padding = 'md',
  variant = 'default',
  className,
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        'rounded-2xl transition-all duration-300',
        paddingStyles[padding],
        variantStyles[variant],
        hover && 'hover:shadow-lg hover:-translate-y-0.5 cursor-pointer',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export interface CardHeaderProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function CardHeader({ title, subtitle, children, action, className }: CardHeaderProps) {
  return (
    <div className={cn('flex items-center justify-between mb-4', className)}>
      <div className="min-w-0 flex-1">
        <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-50 truncate">
                        {children ?? title}

        </h3>
        {subtitle && (
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5 truncate">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div className="shrink-0 ml-4 rtl:ml-0 rtl:mr-4">{action}</div>}
    </div>
  );
}

export interface CardBodyProps {
  children: ReactNode;
  className?: string;
}

export function CardBody({ children, className }: CardBodyProps) {
  return <div className={cn('', className)}>{children}</div>;
}

export interface CardFooterProps {
  children: ReactNode;
  className?: string;
  divider?: boolean;
}

export function CardFooter({ children, className, divider = true }: CardFooterProps) {
  return (
    <div
      className={cn(
        'mt-4 pt-4 flex items-center gap-3',
        divider && 'border-t border-neutral-100 dark:border-neutral-700',
        className,
      )}
    >
      {children}
    </div>
  );
}
