import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { useTranslation } from 'react-i18next';

export function DashboardLayout() {
  const { i18n } = useTranslation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const isRtl = i18n.language === 'ar';

  return (
    <div className="min-h-screen bg-background">
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      <TopBar onMenuToggle={() => setSidebarCollapsed(!sidebarCollapsed)} onSearchToggle={() => {}} />
      <main className={cn(
        'pt-16 min-h-screen transition-all duration-300',
        sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64',
      )}>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
