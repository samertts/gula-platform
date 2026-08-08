import { forwardRef, useState, useRef, useEffect, type SelectHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  icon?: ReactNode;
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  selectSize?: 'sm' | 'md' | 'lg';
  clearable?: boolean;
}

const selectSizeStyles = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-4 py-2.5 text-sm rounded-xl',
  lg: 'px-5 py-3 text-base rounded-2xl',
};

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      error,
      helperText,
      options,
      placeholder,
      selectSize = 'md',
      clearable = false,
      className,
      id,
      value,
      ...props
    },
    ref,
  ) => {
    const selectId = id || `select-${label?.toLowerCase().replace(/\s+/g, '-')}`;
    const hasError = !!error;
    const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

    return (
      <div className={cn('w-full', className)}>
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            value={value}
            aria-invalid={hasError}
            aria-describedby={hasError ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined}
            className={cn(
              'w-full font-medium transition-all duration-200 appearance-none cursor-pointer',
              'border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800',
              'focus:outline-none focus:border-primary-500 dark:focus:border-primary-400',
              'focus:ring-4 focus:ring-primary-100 dark:focus:ring-primary-900/30',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              selectSizeStyles[selectSize],
              hasError && 'border-danger-500 focus:border-danger-500 focus:ring-danger-100',
              isRtl ? 'pl-10 pr-4' : 'pr-10 pl-4',
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map(opt => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </select>
          <span
            className={cn(
              'absolute top-1/2 -translate-y-1/2 pointer-events-none text-neutral-400 transition-transform',
              isRtl ? 'left-3.5' : 'right-3.5',
            )}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
        </div>
        {(error || helperText) && (
          <p
            id={error ? `${selectId}-error` : `${selectId}-helper`}
            className={cn(
              'mt-1.5 text-sm',
              error ? 'text-danger-600 dark:text-danger-400 font-medium' : 'text-neutral-500',
            )}
            role={error ? 'alert' : undefined}
          >
            {error || helperText}
          </p>
        )}
      </div>
    );
  },
);

Select.displayName = 'Select';
