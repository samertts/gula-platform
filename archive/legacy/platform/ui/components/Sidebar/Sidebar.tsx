import { useState, type ReactNode, type MouseEvent } from 'react';
import { cn } from '../../utils/cn';

export interface SidebarItem {
  id: string;
  label: string;
  icon?: ReactNode;
  href?: string;
  onClick?: () => void;
  badge?: string | number;
  active?: boolean;
  disabled?: boolean;
  children?: SidebarItem[];
}

export interface SidebarSection {
  id: string;
  title?: string;
  items: SidebarItem[];
}

export interface SidebarProps {
  sections: SidebarSection[];
  logo?: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  onToggle?: (collapsed: boolean) => void;
  className?: string;
  width?: string;
  collapsedWidth?: string;
}

export function Sidebar({
  sections,
  logo,
  header,
  footer,
  collapsible = false,
  defaultCollapsed = false,
  onToggle,
  className,
  width = 'w-72',
  collapsedWidth = 'w-18',
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  const handleToggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    onToggle?.(next);
  };

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const renderItem = (item: SidebarItem, depth = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.id);

    return (
      <div key={item.id}>
        <button
          onClick={(e) => {
            if (hasChildren) {
              e.preventDefault();
              toggleExpand(item.id);
            }
            item.onClick?.();
          }}
          disabled={item.disabled}
          title={collapsed ? item.label : undefined}
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
            item.active
              ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-200',
            item.disabled && 'opacity-50 cursor-not-allowed',
            collapsed && 'justify-center px-0',
            depth > 0 && 'pl-8 rtl:pl-0 rtl:pr-8',
          )}
          role={hasChildren ? 'button' : undefined}
          aria-expanded={hasChildren ? isExpanded : undefined}
        >
          {item.icon && (
            <span className="shrink-0 w-5 h-5 flex items-center justify-center">
              {item.icon}
            </span>
          )}
          {!collapsed && (
            <>
              <span className="flex-1 text-left rtl:text-right truncate">{item.label}</span>
              {item.badge !== undefined && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
                  {item.badge}
                </span>
              )}
              {hasChildren && (
                <span className={cn('transition-transform', isExpanded && 'rotate-90')}>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
              )}
            </>
          )}
        </button>
        {hasChildren && isExpanded && !collapsed && (
          <div className="ml-2 rtl:ml-0 rtl:mr-2 border-l-2 border-neutral-100 dark:border-neutral-700 pl-2 rtl:pl-0 rtl:pr-2">
            {item.children!.map(child => renderItem(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside
      className={cn(
        'h-full flex flex-col bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 transition-all duration-300',
        collapsed ? collapsedWidth : width,
        isRtl ? 'border-l' : 'border-r',
        className,
      )}
      aria-label="Sidebar navigation"
    >
      {/* Logo/Header */}
      {(logo || collapsible) && (
        <div className={cn(
          'flex items-center p-4 border-b border-neutral-100 dark:border-neutral-800',
          collapsed && 'justify-center',
        )}>
          {!collapsed && logo && <div className="flex-1">{logo}</div>}
          {collapsible && (
            <button
              onClick={handleToggle}
              className="p-2 rounded-xl text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                className={cn('transition-transform', collapsed && 'rotate-180')}
              >
                <path d={isRtl
                  ? "M12 5l-5 5 5 5"
                  : "M8 5l5 5-5 5"
                } stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          )}
        </div>
      )}

      {header && !collapsed && <div className="px-4 py-3">{header}</div>}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6 no-scrollbar">
        {sections.map(section => (
          <div key={section.id}>
            {section.title && !collapsed && (
              <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-widest text-neutral-400 dark:text-neutral-500">
                {section.title}
              </p>
            )}
            <div className="space-y-1">
              {section.items.map(item => renderItem(item))}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      {footer && (
        <div className={cn(
          'border-t border-neutral-100 dark:border-neutral-800 p-4',
          collapsed && 'flex justify-center',
        )}>
          {footer}
        </div>
      )}
    </aside>
  );
}
