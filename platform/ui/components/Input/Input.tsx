import { forwardRef, useState, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export type InputVariant = 'default' | 'filled' | 'flushed';

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  variant?: InputVariant;
  inputSize?: 'sm' | 'md' | 'lg';
  clearable?: boolean;
  onClear?: () => void;
}

const variantStyles: Record<InputVariant, string> = {
  default:
    'border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 focus:border-primary-500 dark:focus:border-primary-400 focus:ring-4 focus:ring-primary-100 dark:focus:ring-primary-900/30',
  filled:
    'border-0 bg-neutral-100 dark:bg-neutral-700 focus:bg-white dark:focus:bg-neutral-800 focus:ring-4 focus:ring-primary-100 dark:focus:ring-primary-900/30',
  flushed:
    'border-0 border-b-2 border-neutral-300 dark:border-neutral-600 rounded-none bg-transparent px-0 focus:border-primary-500 dark:focus:border-primary-400 focus:ring-0',
};

const sizeStyles: Record<string, string> = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-4 py-2.5 text-sm rounded-xl',
  lg: 'px-5 py-3 text-base rounded-2xl',
};

const iconSizeStyles: Record<string, string> = {
  sm: 'px-8',
  md: 'px-10',
  lg: 'px-12',
};

const iconPositionStyles: Record<string, { left: string; right: string }> = {
  sm: { left: 'left-2.5', right: 'right-2.5' },
  md: { left: 'left-3.5', right: 'right-3.5' },
  lg: { left: 'left-4', right: 'right-4' },
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      leftIcon,
      rightIcon,
      variant = 'default',
      inputSize = 'md',
      clearable = false,
      onClear,
      className,
      disabled,
      value,
      defaultValue,
      onChange,
      id,
      ...props
    },
    ref,
  ) => {
    const [focused, setFocused] = useState(false);
    const [localValue, setLocalValue] = useState(defaultValue ?? '');
    const isControlled = value !== undefined;
    const currentValue = isControlled ? value : localValue;
    const inputId = id || `input-${label?.toLowerCase().replace(/\s+/g, '-')}`;
    const hasError = !!error;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!isControlled) setLocalValue(e.target.value);
      onChange?.(e);
    };

    const handleClear = () => {
      if (!isControlled) setLocalValue('');
      if (onClear) onClear();
      const synthetic = { target: { value: '' } } as React.ChangeEvent<HTMLInputElement>;
      onChange?.(synthetic);
    };

    const hasLeftIcon = !!leftIcon;
    const hasRightIcon = !!rightIcon || (clearable && currentValue);

    const iconPos = iconPositionStyles[inputSize];

    return (
      <div className={cn('w-full', className)}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span
              className={cn(
                'absolute top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none',
                iconPos.left,
              )}
            >
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            value={isControlled ? value : undefined}
            defaultValue={!isControlled ? defaultValue : undefined}
            onChange={handleChange}
            onFocus={e => {
              setFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={e => {
              setFocused(false);
              props.onBlur?.(e);
            }}
            disabled={disabled}
            aria-invalid={hasError}
            aria-describedby={hasError ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
            className={cn(
              'w-full font-medium transition-all duration-200',
              'placeholder:text-neutral-400 dark:placeholder:text-neutral-500',
              'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-neutral-50 dark:disabled:bg-neutral-900',
              'focus:outline-none',
              variantStyles[variant],
              sizeStyles[inputSize],
              hasLeftIcon && iconSizeStyles[inputSize],
              (hasRightIcon) && iconSizeStyles[inputSize],
              hasError && 'border-danger-500 focus:border-danger-500 focus:ring-danger-100 dark:focus:ring-danger-900/30',
              props.type === 'search' && 'appearance-none',
            )}
            {...props}
          />
          <div className={cn(
            'absolute top-1/2 -translate-y-1/2 flex items-center gap-1',
            iconPos.right,
          )}>
            {clearable && currentValue && (
              <button
                type="button"
                onClick={handleClear}
                tabIndex={-1}
                className="p-0.5 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
                aria-label="Clear input"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            )}
            {rightIcon && (
              <span className="text-neutral-400 pointer-events-none">{rightIcon}</span>
            )}
          </div>
        </div>
        {(error || helperText) && (
          <p
            id={error ? `${inputId}-error` : `${inputId}-helper`}
            className={cn(
              'mt-1.5 text-sm',
              error ? 'text-danger-600 dark:text-danger-400 font-medium' : 'text-neutral-500 dark:text-neutral-400',
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

Input.displayName = 'Input';
