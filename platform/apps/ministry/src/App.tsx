import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, I18nProvider, ErrorBoundary, Layout, Sidebar, Header, cn, StatusIndicator, useRTL } from '@gula/ui-platform';
import { MinistryProvider } from './contexts/MinistryContext';
import { api } from './services/api';

import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { DiseaseSurveillance } from './pages/DiseaseSurveillance';
import { LabStatistics } from './pages/LabStatistics';
import { HospitalStatistics } from './pages/HospitalStatistics';
import { ResourceMonitoring } from './pages/ResourceMonitoring';
import { RegionalAnalytics } from './pages/RegionalAnalytics';
import { Alerts } from './pages/Alerts';
import { NationalReports } from './pages/NationalReports';
import { VaccinationCoverage } from './pages/VaccinationCoverage';
import { Mortality } from './pages/Mortality';
import { BirthRegistration } from './pages/BirthRegistration';
import { Workforce } from './pages/Workforce';
import { MedicationSupply } from './pages/MedicationSupply';
import { BloodSupply } from './pages/BloodSupply';
import { EmergencyResponse } from './pages/EmergencyResponse';
import { Settings } from './pages/Settings';

const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  SURVEILLANCE: '/surveillance',
  LABS: '/labs',
  HOSPITALS: '/hospitals',
  RESOURCES: '/resources',
  REGIONAL: '/regional',
  ALERTS: '/alerts',
  REPORTS: '/reports',
  VACCINATION: '/vaccination',
  MORTALITY: '/mortality',
  BIRTHS: '/births',
  WORKFORCE: '/workforce',
  MEDICATIONS: '/medications',
  BLOOD: '/blood',
  EMERGENCY: '/emergency',
  SETTINGS: '/settings',
};

const SIDEBAR_SECTIONS = [
  {
    id: 'main',
    label: 'الرئيسية',
    items: [
      { id: 'dashboard', label: 'لوحة القيادة', path: ROUTES.DASHBOARD, icon: 'LayoutDashboard' },
      { id: 'alerts', label: 'الإنذارات', path: ROUTES.ALERTS, icon: 'Bell' },
      { id: 'regional', label: 'التحليلات الإقليمية', path: ROUTES.REGIONAL, icon: 'Map' },
    ],
  },
  {
    id: 'monitoring',
    label: 'الرقابة الصحية',
    items: [
      { id: 'surveillance', label: 'الترصد الوبائي', path: ROUTES.SURVEILLANCE, icon: 'Activity' },
      { id: 'vaccination', label: 'التطعيم', path: ROUTES.VACCINATION, icon: 'Syringe' },
      { id: 'mortality', label: 'الوفيات', path: ROUTES.MORTALITY, icon: 'Heart' },
      { id: 'births', label: 'المواليد', path: ROUTES.BIRTHS, icon: 'Baby' },
    ],
  },
  {
    id: 'resources',
    label: 'الموارد',
    items: [
      { id: 'hospitals', label: 'المستشفيات', path: ROUTES.HOSPITALS, icon: 'Building2' },
      { id: 'labs', label: 'المختبرات', path: ROUTES.LABS, icon: 'Microscope' },
      { id: 'workforce', label: 'القوى العاملة', path: ROUTES.WORKFORCE, icon: 'Users' },
      { id: 'medications', label: 'الأدوية', path: ROUTES.MEDICATIONS, icon: 'Pill' },
      { id: 'blood', label: 'الدم', path: ROUTES.BLOOD, icon: 'Droplets' },
      { id: 'resources', label: 'الموارد', path: ROUTES.RESOURCES, icon: 'Package' },
    ],
  },
  {
    id: 'operations',
    label: 'العمليات',
    items: [
      { id: 'emergency', label: 'الطوارئ', path: ROUTES.EMERGENCY, icon: 'AlertTriangle' },
      { id: 'reports', label: 'التقارير', path: ROUTES.REPORTS, icon: 'FileText' },
      { id: 'settings', label: 'الإعدادات', path: ROUTES.SETTINGS, icon: 'Settings' },
    ],
  },
];

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isRtl } = useRTL(true);
  const [authState, setAuthState] = useState<'checking' | 'authenticated' | 'demo' | 'unauthenticated'>('checking');

  useEffect(() => {
    let active = true;
    const demoEnabled = import.meta.env.VITE_DEMO_MODE === 'true';
    const demoRequested = sessionStorage.getItem('gula_ministry_demo_mode') === 'enabled';

    if (demoEnabled && demoRequested) {
      setAuthState('demo');
      return () => { active = false; };
    }

    api.getSession()
      .then(() => { if (active) setAuthState('authenticated'); })
      .catch(() => { if (active) setAuthState('unauthenticated'); });

    return () => { active = false; };
  }, []);

  if (authState === 'checking') {
    return <div className="min-h-screen bg-slate-950 text-slate-300 flex items-center justify-center" dir="rtl">جارٍ التحقق من جلسة الوزارة…</div>;
  }

  if (authState === 'unauthenticated') return <Navigate to={ROUTES.LOGIN} replace />;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100" dir={isRtl ? 'rtl' : 'ltr'}>
      {authState === 'demo' && (
        <div className="border-b border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-center text-xs text-emerald-200">
          وضع Demo معزول — البيانات اصطناعية، ولا توجد جلسة أو اتصالات إنتاجية.
        </div>
      )}
      <Layout
        sidebar={
          <Sidebar
            sections={SIDEBAR_SECTIONS}
            collapsible
            logo={
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">G</div>
                <span className="font-bold text-white">GULA وزارة</span>
              </div>
            }
          />
        }
      >
        {children}
      </Layout>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <I18nProvider defaultLocale="ar">
          <MinistryProvider>
            <BrowserRouter>
              <Routes>
                <Route path={ROUTES.LOGIN} element={<Login />} />
                <Route path={ROUTES.DASHBOARD} element={<ProtectedLayout><Dashboard /></ProtectedLayout>} />
                <Route path={ROUTES.SURVEILLANCE} element={<ProtectedLayout><DiseaseSurveillance /></ProtectedLayout>} />
                <Route path={ROUTES.LABS} element={<ProtectedLayout><LabStatistics /></ProtectedLayout>} />
                <Route path={ROUTES.HOSPITALS} element={<ProtectedLayout><HospitalStatistics /></ProtectedLayout>} />
                <Route path={ROUTES.RESOURCES} element={<ProtectedLayout><ResourceMonitoring /></ProtectedLayout>} />
                <Route path={ROUTES.REGIONAL} element={<ProtectedLayout><RegionalAnalytics /></ProtectedLayout>} />
                <Route path={ROUTES.ALERTS} element={<ProtectedLayout><Alerts /></ProtectedLayout>} />
                <Route path={ROUTES.REPORTS} element={<ProtectedLayout><NationalReports /></ProtectedLayout>} />
                <Route path={ROUTES.VACCINATION} element={<ProtectedLayout><VaccinationCoverage /></ProtectedLayout>} />
                <Route path={ROUTES.MORTALITY} element={<ProtectedLayout><Mortality /></ProtectedLayout>} />
                <Route path={ROUTES.BIRTHS} element={<ProtectedLayout><BirthRegistration /></ProtectedLayout>} />
                <Route path={ROUTES.WORKFORCE} element={<ProtectedLayout><Workforce /></ProtectedLayout>} />
                <Route path={ROUTES.MEDICATIONS} element={<ProtectedLayout><MedicationSupply /></ProtectedLayout>} />
                <Route path={ROUTES.BLOOD} element={<ProtectedLayout><BloodSupply /></ProtectedLayout>} />
                <Route path={ROUTES.EMERGENCY} element={<ProtectedLayout><EmergencyResponse /></ProtectedLayout>} />
                <Route path={ROUTES.SETTINGS} element={<ProtectedLayout><Settings /></ProtectedLayout>} />
                <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
              </Routes>
            </BrowserRouter>
          </MinistryProvider>
        </I18nProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
