import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider, I18nProvider, ErrorBoundary, Layout, Sidebar, Header } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PatientProvider } from './contexts/PatientContext';
import { ClinicalProvider } from './contexts/ClinicalContext';
import { OfflineProvider } from './contexts/OfflineContext';
import { OfflineIndicator } from './components/OfflineIndicator';

import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { PatientSearch } from './pages/PatientSearch';
import { PatientDetail } from './pages/PatientDetail';
import { ClinicalTimeline } from './pages/ClinicalTimeline';
import { Visits } from './pages/Visits';
import { Diagnoses } from './pages/Diagnoses';
import { Orders } from './pages/Orders';
import { Prescriptions } from './pages/Prescriptions';
import { LabRequests } from './pages/LabRequests';
import { RadiologyRequests } from './pages/RadiologyRequests';
import { DecisionSupport } from './pages/DecisionSupport';
import { DigitalSignature } from './pages/DigitalSignature';
import { VoiceDictation } from './pages/VoiceDictation';
import { OfflineMode } from './pages/OfflineMode';
import { Settings } from './pages/Settings';
import { Referrals } from './pages/Referrals';
import { Telemedicine } from './pages/Telemedicine';
import { Schedule } from './pages/Schedule';
import { Notifications } from './pages/Notifications';

const sidebarSections = [
  {
    id: 'main',
    title: 'القائمة الرئيسية',
    items: [
      { id: 'dashboard', label: 'لوحة المعلومات', path: '/dashboard' },
      { id: 'patients', label: 'المرضى', path: '/patients' },
      { id: 'schedule', label: 'المواعيد', path: '/schedule' },
      { id: 'prescriptions', label: 'الوصفات الطبية', path: '/prescriptions' },
    ],
  },
  {
    id: 'clinical',
    title: 'السريريات',
    items: [
      { id: 'decision-support', label: 'دعم القرار', path: '/decision-support' },
      { id: 'referrals', label: 'التحويلات', path: '/referrals' },
      { id: 'telemedicine', label: 'الاستشارات عن بعد', path: '/telemedicine' },
    ],
  },
  {
    id: 'tools',
    title: 'الأدوات',
    items: [
      { id: 'voice', label: 'الإملاء الصوتي', path: '/voice-dictation' },
      { id: 'signature', label: 'التوقيع الرقمي', path: '/digital-signature' },
      { id: 'offline', label: 'الوضع غير المتصل', path: '/offline' },
    ],
  },
  {
    id: 'system',
    title: 'النظام',
    items: [
      { id: 'notifications', label: 'الإشعارات', path: '/notifications' },
      { id: 'settings', label: 'الإعدادات', path: '/settings' },
    ],
  },
];

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const { isRtl } = useRTL(true);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-neutral-900">
        <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <OfflineIndicator />
      <Layout
        sidebar={
          <Sidebar
            sections={sidebarSections}
            collapsible
            logo={
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">G</div>
                <span className="font-bold text-neutral-900 dark:text-neutral-50">GULA طبيب</span>
              </div>
            }
            footer={
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-bold text-sm">
                  د
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50 truncate">د. أحمد</p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">استشاري باطنية</p>
                </div>
              </div>
            }
          />
        }
        header={
          <Header
            title="GULA طبيب"
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
        <Route path="/patients" element={<PatientSearch />} />
        <Route path="/patients/:patientId" element={<PatientDetail />} />
        <Route path="/patients/:patientId/timeline" element={<ClinicalTimeline />} />
        <Route path="/patients/:patientId/visits" element={<Visits />} />
        <Route path="/patients/:patientId/diagnoses" element={<Diagnoses />} />
        <Route path="/patients/:patientId/orders" element={<Orders />} />
        <Route path="/patients/:patientId/lab-requests" element={<LabRequests />} />
        <Route path="/patients/:patientId/radiology" element={<RadiologyRequests />} />
        <Route path="/prescriptions" element={<Prescriptions />} />
        <Route path="/decision-support" element={<DecisionSupport />} />
        <Route path="/digital-signature" element={<DigitalSignature />} />
        <Route path="/voice-dictation" element={<VoiceDictation />} />
        <Route path="/offline" element={<OfflineMode />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/referrals" element={<Referrals />} />
        <Route path="/telemedicine" element={<Telemedicine />} />
        <Route path="/schedule" element={<Schedule />} />
        <Route path="/notifications" element={<Notifications />} />
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
            <PatientProvider>
              <ClinicalProvider>
                <OfflineProvider>
                  <BrowserRouter>
                    <AppRoutes />
                  </BrowserRouter>
                </OfflineProvider>
              </ClinicalProvider>
            </PatientProvider>
          </AuthProvider>
        </I18nProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
