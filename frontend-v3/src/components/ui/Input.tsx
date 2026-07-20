import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-on-surface">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={id}
        className={cn(
          'flex h-10 w-full rounded-lg border bg-surface px-3 py-2 text-sm placeholder:text-on-surface-variant/60',
          'focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary',
          'disabled:cursor-not-allowed disabled:opacity-50',
          error ? 'border-error focus:ring-error/40' : 'border-outline',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-error">{error}</p>}
    </div>
  )
);
Input.displayName = 'Input';
