import React from 'react';
import { cn } from '../utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success' | 'warning';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const variantStyles: Record<string, string> = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 focus-visible:ring-primary-500 shadow-sm',
  secondary: 'bg-secondary-600 text-white hover:bg-secondary-700 active:bg-secondary-800 focus-visible:ring-secondary-500 shadow-sm',
  outline: 'border-2 border-primary-600 text-primary-700 hover:bg-primary-50 active:bg-primary-100 focus-visible:ring-primary-500',
  ghost: 'text-neutral-700 hover:bg-neutral-100 active:bg-neutral-200 focus-visible:ring-primary-500',
  danger: 'bg-error-600 text-white hover:bg-error-700 active:bg-error-800 focus-visible:ring-error-500 shadow-sm',
  success: 'bg-success-600 text-white hover:bg-success-700 active:bg-success-800 focus-visible:ring-success-500 shadow-sm',
  warning: 'bg-warning-500 text-white hover:bg-warning-600 active:bg-warning-700 focus-visible:ring-warning-500 shadow-sm',
};

const sizeStyles: Record<string, string> = {
  xs: 'px-2 py-1 text-xs gap-1 h-6',
  sm: 'px-3 py-1.5 text-sm gap-1.5 h-8',
  md: 'px-4 py-2 text-sm gap-2 h-10',
  lg: 'px-5 py-2.5 text-base gap-2 h-12',
  xl: 'px-6 py-3 text-lg gap-2.5 h-14',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    variant = 'primary',
    size = 'md',
    loading = false,
    icon,
    iconPosition = 'left',
    fullWidth = false,
    disabled,
    className,
    children,
    ...props
  }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-lg',
        'transition-all duration-150 ease-in-out',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && 'w-full',
        className
      )}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : icon && iconPosition === 'left' ? (
        <span className="inline-flex shrink-0">{icon}</span>
      ) : null}
      {children && <span>{children}</span>}
      {icon && iconPosition === 'right' && !loading ? (
        <span className="inline-flex shrink-0">{icon}</span>
      ) : null}
    </button>
  )
);
Button.displayName = 'Button';

export const IconButton = React.forwardRef<HTMLButtonElement, Omit<ButtonProps, 'iconPosition' | 'fullWidth'>>(
  ({ size = 'md', variant = 'ghost', className, children, ...props }, ref) => (
    <Button
      ref={ref}
      variant={variant}
      size={size}
      className={cn('p-0 aspect-square', className)}
      {...props}
    >
      {children}
    </Button>
  )
);
IconButton.displayName = 'IconButton';
