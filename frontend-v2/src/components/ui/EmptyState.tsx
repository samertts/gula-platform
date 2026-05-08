import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { Inbox } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface EmptyStateAction {
  label: string;
  onClick?: () => void;
  href?: string;
  /** Visual style. `primary` for the recommended next step, `secondary` for alts. */
  variant?: 'primary' | 'secondary';
}

interface EmptyStateProps {
  /** Headline. One short sentence. */
  title: string;
  /** Optional sub-headline that explains *why* the surface is empty. */
  description?: ReactNode;
  /** Lucide icon component. Defaults to a generic inbox glyph. */
  icon?: LucideIcon;
  /** Up to two CTAs. The first becomes primary if no variant is set. */
  actions?: EmptyStateAction[];
  /** Optional contextual hint rendered below the actions in muted text. */
  hint?: ReactNode;
  className?: string;
  /** Compact variant — for small inline empty surfaces (filters, panels). */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Reusable empty-state surface with actionable next steps.
 *
 * Use anywhere a list, table, or panel can render zero items. Always provide
 * at least one action so the user is never stuck on a dead-end screen.
 */
export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  actions = [],
  hint,
  className,
  size = 'md',
}: EmptyStateProps) {
  const sizeClasses = {
    sm: 'p-8 gap-3',
    md: 'p-12 gap-4',
    lg: 'p-16 gap-5',
  }[size];
  const iconSize = { sm: 28, md: 36, lg: 48 }[size];
  const iconBox = { sm: 'h-14 w-14', md: 'h-20 w-20', lg: 'h-24 w-24' }[size];

  return (
    <div
      role="status"
      className={cn(
        'flex flex-col items-center text-center bg-white rounded-2xl border border-slate-100',
        sizeClasses,
        className,
      )}
      data-testid="empty-state"
    >
      <div
        className={cn(
          'rounded-3xl bg-slate-50 flex items-center justify-center text-slate-300',
          iconBox,
        )}
        aria-hidden="true"
      >
        <Icon size={iconSize} strokeWidth={1.5} />
      </div>
      <h3 className="font-headline text-lg sm:text-xl font-black text-slate-900 tracking-tight">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-slate-500 max-w-md leading-relaxed">{description}</p>
      )}
      {actions.length > 0 && (
        <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
          {actions.map((action, i) => {
            const variant =
              action.variant ?? (i === 0 ? 'primary' : 'secondary');
            const baseClasses =
              'px-5 py-2.5 rounded-xl text-sm font-bold transition-all active:scale-95 shadow-sm';
            const variantClasses =
              variant === 'primary'
                ? 'bg-indigo-600 text-white shadow-indigo-100 hover:bg-indigo-700'
                : 'bg-slate-50 text-slate-700 border border-slate-100 hover:bg-slate-100';
            if (action.href) {
              return (
                <a
                  key={i}
                  href={action.href}
                  className={cn(baseClasses, variantClasses)}
                >
                  {action.label}
                </a>
              );
            }
            return (
              <button
                key={i}
                type="button"
                onClick={action.onClick}
                className={cn(baseClasses, variantClasses)}
              >
                {action.label}
              </button>
            );
          })}
        </div>
      )}
      {hint && (
        <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mt-1">
          {hint}
        </p>
      )}
    </div>
  );
}
