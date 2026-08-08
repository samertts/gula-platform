import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider, I18nProvider, ErrorBoundary, Layout, Sidebar, Header, cn, StatusIndicator } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { LabProvider, useLab } from './contexts/LabContext';
import { WorklistProvider } from './contexts/WorklistContext';
import { OfflineProvider, useOffline } from './contexts/OfflineContext';

import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { SampleCollection } from './pages/SampleCollection';
import { Receiving } from './pages/Receiving';
import { SampleTracking } from './pages/SampleTracking';
import { QualityControl } from './pages/QualityControl';
import { ResultValidation } from './pages/ResultValidation';
import { Autoverification } from './pages/Autoverification';
import { Microbiology } from './pages/Microbiology';
import { Molecular } from './pages/Molecular';
import { BloodBank } from './pages/BloodBank';
import { Histopathology } from './pages/Histopathology';
import { AnalyzerIntegration } from './pages/AnalyzerIntegration';
import { BarcodePrinting } from './pages/BarcodePrinting';
import { Reports } from './pages/Reports';
import { Inventory } from './pages/Inventory';
import { Worklist } from './pages/Worklist';
import { InstrumentMonitor } from './pages/InstrumentMonitor';
import { OfflineMode } from './pages/OfflineMode';
import { Settings } from './pages/Settings';
import { AuditLog } from './pages/AuditLog';
import { ROUTES, SIDEBAR_SECTIONS } from './utils/routes';

function ProtectedLayout() {
  const { isAuthenticated, isLoading, user } = useLab();
  const { isRtl } = useRTL(true);
  const { isOnline, pendingCount, lastSync } = useOffline();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-neutral-500">جاري التحميل...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      {!isOnline && (
        <div className="sticky top-0 z-50 bg-warning-500 text-white text-center py-1.5 text-xs font-bold">
          لا يوجد اتصال بالإنترنت - البيانات تعمل في وضع عدم الاتصال
          {pendingCount > 0 && ` (${pendingCount} عملية معلقة)`}
        </div>
      )}

      <Layout
        sidebar={
          <Sidebar
            sections={SIDEBAR_SECTIONS}
            collapsible
            logo={
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">G</div>
                <span className="font-bold text-neutral-900 dark:text-neutral-50">GULA مختبر</span>
              </div>
            }
            footer={
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className={cn(
                    'w-2 h-2 rounded-full',
                    isOnline ? 'bg-success-500' : 'bg-warning-500 animate-pulse',
                  )} />
                  <span className="text-xs text-neutral-400 dark:text-neutral-500">
                    {isOnline ? 'متصل' : 'غير متصل'}
                    {pendingCount > 0 && ` (${pendingCount})`}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-bold text-sm">
                    {user?.name?.charAt(0) || 'م'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50 truncate">{user?.name || 'مستخدم'}</p>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">{roleArabic(user?.role || 'technician')}</p>
                  </div>
                </div>
              </div>
            }
          />
        }
        header={
          <Header
            title="GULA مختبر"
            onMenuClick={() => {}}
            breadcrumbs={[{ label: 'المختبر', href: ROUTES.DASHBOARD }]}
          />
        }
      >
        <Outlet />
      </Layout>
    </div>
  );
}

function roleArabic(role: string): string {
  const roles: Record<string, string> = {
    technician: 'فني مختبر',
    senior_technician: 'فني أول',
    pathologist: 'أخصائي علم الأمراض',
    lab_manager: 'مدير مختبر',
    admin: 'مسؤول النظام',
    phlebotomist: 'فني سحب عينات',
  };
  return roles[role] || role;
}

function AppRoutes() {
  const { isAuthenticated, isLoading } = useLab();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-neutral-500">جاري تحميل التطبيق...</span>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={isAuthenticated ? <Navigate to={ROUTES.DASHBOARD} replace /> : <Login />} />

      <Route element={<ProtectedLayout />}>
        <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
        <Route path={ROUTES.WORKLIST} element={<Worklist />} />
        <Route path={ROUTES.SAMPLE_COLLECTION} element={<SampleCollection />} />
        <Route path={ROUTES.RECEIVING} element={<Receiving />} />
        <Route path={ROUTES.SAMPLE_TRACKING} element={<SampleTracking />} />
        <Route path={ROUTES.RESULT_VALIDATION} element={<ResultValidation />} />
        <Route path={ROUTES.AUTOVERIFICATION} element={<Autoverification />} />
        <Route path={ROUTES.QUALITY_CONTROL} element={<QualityControl />} />
        <Route path={ROUTES.MICROBIOLOGY} element={<Microbiology />} />
        <Route path={ROUTES.MOLECULAR} element={<Molecular />} />
        <Route path={ROUTES.BLOOD_BANK} element={<BloodBank />} />
        <Route path={ROUTES.HISTOPATHOLOGY} element={<Histopathology />} />
        <Route path={ROUTES.ANALYZER_INTEGRATION} element={<AnalyzerIntegration />} />
        <Route path={ROUTES.INSTRUMENT_MONITOR} element={<InstrumentMonitor />} />
        <Route path={ROUTES.INVENTORY} element={<Inventory />} />
        <Route path={ROUTES.REPORTS} element={<Reports />} />
        <Route path={ROUTES.BARCODE_PRINTING} element={<BarcodePrinting />} />
        <Route path={ROUTES.OFFLINE_MODE} element={<OfflineMode />} />
        <Route path={ROUTES.AUDIT_LOG} element={<AuditLog />} />
        <Route path={ROUTES.SETTINGS} element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultRtl>
        <I18nProvider defaultLocale="ar">
          <LabProvider>
            <WorklistProvider>
              <OfflineProvider>
                <BrowserRouter>
                  <AppRoutes />
                </BrowserRouter>
              </OfflineProvider>
            </WorklistProvider>
          </LabProvider>
        </I18nProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
