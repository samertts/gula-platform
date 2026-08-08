import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../utils/cn';
import { LoadingSpinner } from '../LoadingSpinner/LoadingSpinner';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700 shadow-sm hover:shadow-md focus-visible:ring-4 focus-visible:ring-primary-200',
  secondary:
    'bg-neutral-100 text-neutral-800 hover:bg-neutral-200 active:bg-neutral-300 focus-visible:ring-4 focus-visible:ring-neutral-200 dark:bg-neutral-700 dark:text-neutral-100 dark:hover:bg-neutral-600',
  outline:
    'border-2 border-primary-500 text-primary-600 hover:bg-primary-50 active:bg-primary-100 focus-visible:ring-4 focus-visible:ring-primary-200 dark:border-primary-400 dark:text-primary-400 dark:hover:bg-primary-950',
  ghost:
    'text-neutral-600 hover:bg-neutral-100 active:bg-neutral-200 focus-visible:ring-4 focus-visible:ring-neutral-200 dark:text-neutral-400 dark:hover:bg-neutral-800',
  danger:
    'bg-danger-500 text-white hover:bg-danger-600 active:bg-danger-700 shadow-sm focus-visible:ring-4 focus-visible:ring-danger-200',
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: 'px-2.5 py-1 text-xs rounded-lg gap-1.5',
  sm: 'px-3.5 py-1.5 text-sm rounded-xl gap-1.5',
  md: 'px-5 py-2.5 text-sm rounded-xl gap-2',
  lg: 'px-6 py-3 text-base rounded-2xl gap-2',
  xl: 'px-8 py-4 text-lg rounded-2xl gap-2.5',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      icon,
      iconPosition = 'left',
      fullWidth = false,
      disabled,
      className,
      children,
      type = 'button',
      ...props
    },
    ref,
  ) => {
    const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';
    const adjustedIconPos = isRtl ? (iconPosition === 'left' ? 'right' : 'left') : iconPosition;

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || loading}
        className={cn(
          'inline-flex items-center justify-center font-bold transition-all duration-200 ease-out',
          'focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
          'active:scale-[0.97] select-none',
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && 'w-full',
          className,
        )}
        {...props}
      >
        {loading && <LoadingSpinner size="sm" className="shrink-0" />}
        {!loading && icon && adjustedIconPos === 'left' && (
          <span className="shrink-0 [&>svg]:w-4 [&>svg]:h-4">{icon}</span>
        )}
        {children && <span className={cn(loading && 'opacity-0', 'truncate')}>{children}</span>}
        {!loading && icon && adjustedIconPos === 'right' && (
          <span className="shrink-0 [&>svg]:w-4 [&>svg]:h-4">{icon}</span>
        )}
      </button>
    );
  },
);

Button.displayName = 'Button';
