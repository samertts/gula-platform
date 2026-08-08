import { useState, useEffect, useRef, type InputHTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export interface SearchInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value'> {
  value?: string;
  onChange?: (value: string) => void;
  debounceMs?: number;
  onSearch?: (value: string) => void;
  inputSize?: 'sm' | 'md' | 'lg';
  clearable?: boolean;
}

export function SearchInput({
  value: controlledValue,
  onChange,
  debounceMs = 300,
  onSearch,
  placeholder = 'Search...',
  inputSize = 'md',
  clearable = true,
  className,
  ...props
}: SearchInputProps) {
  const [localValue, setLocalValue] = useState(controlledValue ?? '');
  const isControlled = controlledValue !== undefined;
  const currentValue = isControlled ? controlledValue : localValue;
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (debounceMs > 0) {
      debounceRef.current = setTimeout(() => {
        onSearch?.(currentValue);
      }, debounceMs);
      return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    }
  }, [currentValue, debounceMs, onSearch]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (!isControlled) setLocalValue(val);
    onChange?.(val);
  };

  const handleClear = () => {
    if (!isControlled) setLocalValue('');
    onChange?.('');
    onSearch?.('');
    inputRef.current?.focus();
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm rounded-lg pl-9 rtl:pl-3 rtl:pr-9',
    md: 'px-4 py-2.5 text-sm rounded-xl pl-10 rtl:pl-4 rtl:pr-10',
    lg: 'px-5 py-3 text-base rounded-2xl pl-11 rtl:pl-5 rtl:pr-11',
  };

  const iconSizes = {
    sm: 'left-3 rtl:left-auto rtl:right-3',
    md: 'left-3.5 rtl:left-auto rtl:right-3.5',
    lg: 'left-4 rtl:left-auto rtl:right-4',
  };

  return (
    <div className={cn('relative', className)}>
      <span className={cn(
        'absolute top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none',
        iconSizes[inputSize],
      )}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M10.5 10.5l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </span>
      <input
        ref={inputRef}
        type="search"
        value={isControlled ? controlledValue : undefined}
        defaultValue={!isControlled ? undefined : undefined}
        onChange={handleChange}
        placeholder={placeholder}
        aria-label={placeholder}
        className={cn(
          'w-full font-medium transition-all duration-200',
          'border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800',
          'focus:outline-none focus:border-primary-500 dark:focus:border-primary-400',
          'focus:ring-4 focus:ring-primary-100 dark:focus:ring-primary-900/30',
          'placeholder:text-neutral-400 dark:placeholder:text-neutral-500',
          sizeStyles[inputSize],
          clearable && currentValue && 'pr-9 rtl:pr-4 rtl:pl-9',
        )}
        {...props}
      />
      {clearable && currentValue && (
        <button
          type="button"
          onClick={handleClear}
          className={cn(
            'absolute top-1/2 -translate-y-1/2 p-0.5 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors',
            iconSizes[inputSize],
          )}
          aria-label="Clear search"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M10.5 3.5l-7 7M3.5 3.5l7 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </button>
      )}
    </div>
  );
}
