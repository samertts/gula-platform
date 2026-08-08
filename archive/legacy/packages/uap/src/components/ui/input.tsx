import React from 'react';
import { cn } from '../utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  rtl?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, rtl = false, className, id, ...props }, ref) => {
    const inputId = id || `input-${label?.toLowerCase().replace(/\s+/g, '-')}`;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className={cn('block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5', rtl && 'text-right')}>
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'block w-full rounded-lg border px-3 py-2.5 text-sm',
            'bg-white dark:bg-neutral-800',
            'text-neutral-900 dark:text-white',
            'placeholder:text-neutral-400 dark:placeholder:text-neutral-500',
            'transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-neutral-50 dark:disabled:bg-neutral-900',
            error
              ? 'border-error-500 focus:ring-error-500 focus:border-error-500'
              : 'border-neutral-300 dark:border-neutral-600 hover:border-neutral-400 dark:hover:border-neutral-500',
            rtl && 'text-right',
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="mt-1 text-sm text-error-600 dark:text-error-400" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
  rtl?: boolean;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, rtl = false, className, ...props }, ref) => (
    <div className="w-full">
      {label && (
        <label className={cn('block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5', rtl && 'text-right')}>
          {label}
        </label>
      )}
      <select
        ref={ref}
        className={cn(
          'block w-full rounded-lg border px-3 py-2.5 text-sm',
          'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white',
          'transition-colors duration-150',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
          error ? 'border-error-500' : 'border-neutral-300 dark:border-neutral-600',
          rtl && 'text-right',
          className
        )}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && <p className="mt-1 text-sm text-error-600">{error}</p>}
    </div>
  )
);
Select.displayName = 'Select';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  rtl?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, rtl = false, className, ...props }, ref) => (
    <div className="w-full">
      {label && (
        <label className={cn('block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5', rtl && 'text-right')}>
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        className={cn(
          'block w-full rounded-lg border px-3 py-2.5 text-sm',
          'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white',
          'transition-colors duration-150',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
          'resize-y min-h-[80px]',
          error ? 'border-error-500' : 'border-neutral-300 dark:border-neutral-600',
          rtl && 'text-right',
          className
        )}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-error-600">{error}</p>}
    </div>
  )
);
Textarea.displayName = 'Textarea';
