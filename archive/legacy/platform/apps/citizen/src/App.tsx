import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider, I18nProvider, ErrorBoundary } from '@gula/ui-platform';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { HealthProvider } from './contexts/HealthContext';
import { OfflineProvider } from './contexts/OfflineContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { OfflineIndicator } from './components/OfflineIndicator';
import { SyncStatus } from './components/SyncStatus';

import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { HealthID } from './pages/HealthID';
import { DigitalCard } from './pages/DigitalCard';
import { Appointments } from './pages/Appointments';
import { LabResults } from './pages/LabResults';
import { RadiologyReports } from './pages/RadiologyReports';
import { Prescriptions } from './pages/Prescriptions';
import { Vaccinations } from './pages/Vaccinations';
import { MedicalHistory } from './pages/MedicalHistory';
import { Notifications } from './pages/Notifications';
import { QRVerification } from './pages/QRVerification';
import { OfflineWallet } from './pages/OfflineWallet';
import { EmergencyCard } from './pages/EmergencyCard';
import { FamilyAccounts } from './pages/FamilyAccounts';
import { ConsentManagement } from './pages/ConsentManagement';
import { Telemedicine } from './pages/Telemedicine';
import { Payments } from './pages/Payments';
import { Settings } from './pages/Settings';
import { Profile } from './pages/Profile';
import { HealthAssistant } from './pages/HealthAssistant';

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuth();

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
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900 pb-16">
      <OfflineIndicator />
      <Header />
      <SyncStatus />
      <main className="max-w-lg mx-auto">
        <Outlet />
      </main>
      <Navigation />
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
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to="/" replace /> : <Register />} />

      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/health-id" element={<HealthID />} />
        <Route path="/digital-card" element={<DigitalCard />} />
        <Route path="/appointments" element={<Appointments />} />
        <Route path="/lab-results" element={<LabResults />} />
        <Route path="/radiology" element={<RadiologyReports />} />
        <Route path="/prescriptions" element={<Prescriptions />} />
        <Route path="/vaccinations" element={<Vaccinations />} />
        <Route path="/medical-history" element={<MedicalHistory />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/qr-verify" element={<QRVerification />} />
        <Route path="/offline-wallet" element={<OfflineWallet />} />
        <Route path="/emergency-card" element={<EmergencyCard />} />
        <Route path="/family" element={<FamilyAccounts />} />
        <Route path="/consent" element={<ConsentManagement />} />
        <Route path="/telemedicine" element={<Telemedicine />} />
        <Route path="/payments" element={<Payments />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/assistant" element={<HealthAssistant />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultRtl>
        <I18nProvider defaultLocale="ar">
          <AuthProvider>
            <HealthProvider>
              <OfflineProvider>
                <NotificationProvider>
                  <BrowserRouter>
                    <AppRoutes />
                  </BrowserRouter>
                </NotificationProvider>
              </OfflineProvider>
            </HealthProvider>
          </AuthProvider>
        </I18nProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
