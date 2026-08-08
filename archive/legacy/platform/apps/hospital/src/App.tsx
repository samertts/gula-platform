import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider, I18nProvider, ErrorBoundary, Layout, Sidebar, Header } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { Admissions } from './pages/Admissions';
import { Beds } from './pages/Beds';
import { Departments } from './pages/Departments';
import { Assets } from './pages/Assets';
import { Finance } from './pages/Finance';
import { HR } from './pages/HR';
import { Reporting } from './pages/Reporting';
import { Discharge } from './pages/Discharge';
import { OperatingTheatre } from './pages/OperatingTheatre';
import { Clinics } from './pages/Clinics';
import { Inventory } from './pages/Inventory';
import { Maintenance } from './pages/Maintenance';
import { Settings } from './pages/Settings';

const sidebarSections = [
  {
    id: 'main',
    title: 'الرئيسية',
    items: [
      { id: 'dashboard', label: 'لوحة المعلومات', path: '/dashboard' },
      { id: 'admissions', label: 'الاستقبال', path: '/admissions' },
      { id: 'beds', label: 'الأسرة', path: '/beds' },
      { id: 'discharge', label: 'التخريج', path: '/discharge' },
    ],
  },
  {
    id: 'clinical',
    title: 'السريريات',
    items: [
      { id: 'departments', label: 'الأقسام', path: '/departments' },
      { id: 'clinics', label: 'العيادات الخارجية', path: '/clinics' },
      { id: 'operating-theatre', label: 'غرف العمليات', path: '/operating-theatre' },
    ],
  },
  {
    id: 'operations',
    title: 'العمليات',
    items: [
      { id: 'assets', label: 'الأصول والمعدات', path: '/assets' },
      { id: 'inventory', label: 'المخزون', path: '/inventory' },
      { id: 'maintenance', label: 'الصيانة', path: '/maintenance' },
    ],
  },
  {
    id: 'management',
    title: 'الإدارة',
    items: [
      { id: 'finance', label: 'المالية', path: '/finance' },
      { id: 'hr', label: 'الموارد البشرية', path: '/hr' },
      { id: 'reporting', label: 'التقارير', path: '/reporting' },
    ],
  },
  {
    id: 'system',
    title: 'النظام',
    items: [
      { id: 'settings', label: 'الإعدادات', path: '/settings' },
    ],
  },
];

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const { isRtl } = useRTL(true);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900">
        <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <Layout
        sidebar={
          <Sidebar
            sections={sidebarSections}
            collapsible
            logo={
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">G</div>
                <span className="font-bold text-neutral-900 dark:text-neutral-50">GULA مستشفى</span>
              </div>
            }
            footer={
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-bold text-sm">
                  م
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50 truncate">المدير</p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">إدارة المستشفى</p>
                </div>
              </div>
            }
          />
        }
        header={
          <Header
            title="GULA مستشفى"
            onMenuClick={() => {}}
            breadcrumbs={[{ label: 'الرئيسية', href: '/dashboard' }]}
          />
        }
      >
        <Outlet />
      </Layout>
    </div>
  );
}

function PublicLayout() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <Outlet />
    </div>
  );
}

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-neutral-900">
        <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} />
      </Route>

      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/admissions" element={<Admissions />} />
        <Route path="/beds" element={<Beds />} />
        <Route path="/departments" element={<Departments />} />
        <Route path="/assets" element={<Assets />} />
        <Route path="/finance" element={<Finance />} />
        <Route path="/hr" element={<HR />} />
        <Route path="/reporting" element={<Reporting />} />
        <Route path="/discharge" element={<Discharge />} />
        <Route path="/operating-theatre" element={<OperatingTheatre />} />
        <Route path="/clinics" element={<Clinics />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/maintenance" element={<Maintenance />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultRtl>
        <I18nProvider defaultLocale="ar">
          <AuthProvider>
            <BrowserRouter>
              <AppRoutes />
            </BrowserRouter>
          </AuthProvider>
        </I18nProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
