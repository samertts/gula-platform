import { cn } from '../../utils/cn';

export type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface LoadingSpinnerProps {
  size?: SpinnerSize;
  className?: string;
  label?: string;
}

const sizeStyles: Record<SpinnerSize, string> = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

export function LoadingSpinner({ size = 'md', className, label }: LoadingSpinnerProps) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)} role="status">
      <svg
        className={cn('animate-spin text-primary-500', sizeStyles[size])}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {label && <span className="text-sm text-neutral-500 dark:text-neutral-400">{label}</span>}
    </span>
  );
}

export interface LoadingOverlayProps {
  loading: boolean;
  children?: React.ReactNode;
  label?: string;
  spinnerSize?: SpinnerSize;
  className?: string;
}

export function LoadingOverlay({
  loading,
  children,
  label = 'Loading...',
  spinnerSize = 'lg',
  className,
}: LoadingOverlayProps) {
  if (!loading) return <>{children}</>;

  return (
    <div className={cn('relative', className)}>
      {children && <div className="opacity-30 pointer-events-none">{children}</div>}
      <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-neutral-900/50 backdrop-blur-sm rounded-2xl">
        <LoadingSpinner size={spinnerSize} label={label} />
      </div>
    </div>
  );
}
