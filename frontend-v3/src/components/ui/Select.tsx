import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, id, options, placeholder, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-on-surface">
          {label}
        </label>
      )}
      <select
        ref={ref}
        id={id}
        className={cn(
          'flex h-10 w-full rounded-lg border bg-surface px-3 py-2 text-sm',
          'focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary',
          'disabled:cursor-not-allowed disabled:opacity-50',
          error ? 'border-error focus:ring-error/40' : 'border-outline',
          className
        )}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && <p className="text-xs text-error">{error}</p>}
    </div>
  )
);
Select.displayName = 'Select';
