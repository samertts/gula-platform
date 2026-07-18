import { useState, type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  badge?: string | number;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: Tab[];
  activeTab?: string;
  onChange?: (tabId: string) => void;
  variant?: 'underline' | 'pills' | 'segmented';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children?: ReactNode;
}

const variantStyles = {
  underline: {
    container: 'border-b border-neutral-200 dark:border-neutral-700',
    tab: (active: boolean, disabled: boolean) =>
      cn(
        'px-4 py-3 text-sm font-bold border-b-2 -mb-px transition-colors whitespace-nowrap',
        active
          ? 'border-primary-500 text-primary-600 dark:text-primary-400 dark:border-primary-400'
          : 'border-transparent text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300 hover:border-neutral-300',
        disabled && 'opacity-50 cursor-not-allowed',
      ),
  },
  pills: {
    container: 'flex gap-1',
    tab: (active: boolean, disabled: boolean) =>
      cn(
        'px-4 py-2 text-sm font-bold rounded-xl transition-all whitespace-nowrap',
        active
          ? 'bg-primary-500 text-white shadow-sm'
          : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800',
        disabled && 'opacity-50 cursor-not-allowed',
      ),
  },
  segmented: {
    container: 'inline-flex p-1 bg-neutral-100 dark:bg-neutral-800 rounded-2xl',
    tab: (active: boolean, disabled: boolean) =>
      cn(
        'px-4 py-2 text-sm font-bold rounded-xl transition-all whitespace-nowrap',
        active
          ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm'
          : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300',
        disabled && 'opacity-50 cursor-not-allowed',
      ),
  },
};

const sizeStyles = {
  sm: 'text-xs px-3 py-1.5',
  md: 'text-sm px-4 py-2',
  lg: 'text-base px-5 py-2.5',
};

export function Tabs({
  tabs,
  activeTab: controlledActiveTab,
  onChange,
  variant = 'underline',
  size = 'md',
  className,
  children,
}: TabsProps) {
  const [internalActiveTab, setInternalActiveTab] = useState(tabs[0]?.id);
  const activeTab = controlledActiveTab ?? internalActiveTab;

  const handleChange = (tabId: string) => {
    setInternalActiveTab(tabId);
    onChange?.(tabId);
  };

  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  return (
    <div className={cn('w-full', className)}>
      <div
        className={cn(
          'flex items-center',
          variantStyles[variant].container,
          variant === 'underline' && 'overflow-x-auto no-scrollbar',
          isRtl && 'flex-row-reverse',
        )}
        role="tablist"
        aria-orientation="horizontal"
      >
        {tabs.map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-disabled={tab.disabled}
            onClick={() => !tab.disabled && handleChange(tab.id)}
            className={cn(
              variantStyles[variant].tab(activeTab === tab.id, !!tab.disabled),
              sizeStyles[size],
            )}
          >
            <span className="flex items-center gap-2">
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              {tab.label}
              {tab.badge !== undefined && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-neutral-200 dark:bg-neutral-600 text-neutral-700 dark:text-neutral-300">
                  {tab.badge}
                </span>
              )}
            </span>
          </button>
        ))}
      </div>
      {children && (
        <div className="pt-4" role="tabpanel">
          {children}
        </div>
      )}
    </div>
  );
}
