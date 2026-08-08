import { type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export interface HeaderBreadcrumb {
  label: string;
  href?: string;
}

export interface HeaderProps {
  title?: string;
  breadcrumbs?: HeaderBreadcrumb[];
  leftContent?: ReactNode;
  rightContent?: ReactNode;
  variant?: 'default' | 'compact' | 'transparent';
  className?: string;
}

const variantStyles = {
  default: 'bg-white/90 dark:bg-neutral-900/90 backdrop-blur-xl border-b border-neutral-200 dark:border-neutral-800',
  compact: 'bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800',
  transparent: 'bg-transparent',
};

export function Header({
  title,
  breadcrumbs,
  leftContent,
  rightContent,
  variant = 'default',
  className,
}: HeaderProps) {
  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  return (
    <header
      className={cn(
        'sticky top-0 z-30 w-full',
        variantStyles[variant],
        variant === 'default' ? 'h-16' : variant === 'compact' ? 'h-14' : 'h-auto',
        className,
      )}
    >
      <div className="flex items-center justify-between h-full px-4 md:px-6 gap-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {leftContent}

          {breadcrumbs && breadcrumbs.length > 0 && (
            <nav aria-label="Breadcrumb" className="hidden sm:flex items-center gap-1.5 text-sm text-neutral-500 dark:text-neutral-400">
              {breadcrumbs.map((crumb, idx) => (
                <span key={idx} className="flex items-center gap-1.5">
                  {idx > 0 && (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={cn('shrink-0', isRtl ? 'rotate-180' : '')}>
                      <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                  {crumb.href ? (
                    <a
                      href={crumb.href}
                      className="hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors font-medium"
                    >
                      {crumb.label}
                    </a>
                  ) : (
                    <span className="text-neutral-900 dark:text-neutral-100 font-bold">{crumb.label}</span>
                  )}
                </span>
              ))}
            </nav>
          )}

          {title && !breadcrumbs && (
            <h1 className="text-lg font-bold text-neutral-900 dark:text-neutral-50 truncate">
              {title}
            </h1>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {rightContent}
        </div>
      </div>
    </header>
  );
}
