import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { NAV_ITEMS, filterNavByRole } from '@/constants/navigation';
import { ChevronDown, ChevronLeft, Menu, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const location = useLocation();
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set());

  if (!user) return null;

  const navItems = filterNavByRole(NAV_ITEMS, user.role);
  const isRtl = i18n.language === 'ar';

  const toggleMenu = (path: string) => {
    setExpandedMenus((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <>
      {!collapsed && (
        <div className="fixed inset-0 z-30 bg-black/20 lg:hidden" onClick={onToggle} />
      )}
      <aside
        className={cn(
          'fixed top-0 bottom-0 z-40 flex flex-col bg-surface border-outline transition-all duration-300',
          collapsed ? 'w-0 -translate-x-full lg:w-16 lg:translate-x-0' : 'w-64',
          isRtl ? 'right-0 border-l' : 'left-0 border-r'
        )}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-outline">
          {!collapsed && (
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-white font-bold text-sm">G</span>
              </div>
              <span className="font-semibold text-on-surface">{t('appShortName')}</span>
            </Link>
          )}
          {collapsed && (
            <Link to="/dashboard" className="mx-auto">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-white font-bold text-sm">G</span>
              </div>
            </Link>
          )}
          <button onClick={onToggle} className="p-1.5 rounded-lg hover:bg-surface-container-high lg:block hidden">
            <ChevronLeft className={cn('h-4 w-4 transition-transform', collapsed && 'rotate-180')} />
          </button>
          <button onClick={onToggle} className="p-1.5 rounded-lg hover:bg-surface-container-high lg:hidden">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {navItems.map((item) => {
            const active = isActive(item.path);
            const hasChildren = item.children && item.children.length > 0;
            const expanded = expandedMenus.has(item.path);

            if (collapsed) {
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'flex items-center justify-center h-10 w-10 mx-auto rounded-lg transition-colors',
                    active ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container-high'
                  )}
                  title={t(item.labelKey)}
                >
                  <item.icon className="h-5 w-5" />
                </Link>
              );
            }

            return (
              <div key={item.path}>
                <div
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors group',
                    active ? 'bg-primary/10 text-primary font-medium' : 'text-on-surface-variant hover:bg-surface-container-high'
                  )}
                  onClick={() => hasChildren ? toggleMenu(item.path) : undefined}
                >
                  {hasChildren ? (
                    <Link to={item.path} className="flex items-center gap-3 flex-1 min-w-0" onClick={(e) => e.stopPropagation()}>
                      <item.icon className="h-5 w-5 shrink-0" />
                      <span className="text-sm truncate">{t(item.labelKey)}</span>
                    </Link>
                  ) : (
                    <Link to={item.path} className="flex items-center gap-3 flex-1 min-w-0">
                      <item.icon className="h-5 w-5 shrink-0" />
                      <span className="text-sm truncate">{t(item.labelKey)}</span>
                    </Link>
                  )}
                  {hasChildren && (
                    <ChevronDown className={cn('h-4 w-4 transition-transform', expanded && 'rotate-180')} />
                  )}
                </div>
                {hasChildren && expanded && (
                  <div className={cn('ml-2 mt-0.5 space-y-0.5', isRtl ? 'mr-8 ml-0' : 'ml-8')}>
                    {item.children!.map((child) => (
                      <Link
                        key={child.path}
                        to={child.path}
                        className={cn(
                          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                          location.pathname === child.path
                            ? 'bg-primary/10 text-primary font-medium'
                            : 'text-on-surface-variant hover:bg-surface-container-high'
                        )}
                      >
                        <child.icon className="h-4 w-4 shrink-0" />
                        <span className="truncate">{t(child.labelKey)}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
