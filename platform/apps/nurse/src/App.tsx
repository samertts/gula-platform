import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@gula/ui-platform';
import { NurseProvider, useNurse } from './contexts/NurseContext';
import { OfflineProvider } from './contexts/OfflineContext';
import { ROUTES } from './utils/routes';
import { Layout, ProtectedRoute, Sidebar } from '@gula/ui-platform';
import { SIDEBAR_SECTIONS } from './utils/routes';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import MedicationAdministration from './pages/MedicationAdministration';
import VitalSigns from './pages/VitalSigns';
import WardManagement from './pages/WardManagement';
import Admissions from './pages/Admissions';
import Discharge from './pages/Discharge';
import BedsideVerification from './pages/BedsideVerification';
import BarcodeScanning from './pages/BarcodeScanning';
import QRVerification from './pages/QRVerification';
import OfflineMode from './pages/OfflineMode';
import CarePlan from './pages/CarePlan';
import ShiftHandover from './pages/ShiftHandover';
import TaskList from './pages/TaskList';
import PatientRound from './pages/PatientRound';
import Settings from './pages/Settings';

function AppLayout() {
  const { user } = useNurse();
  return (
    <Layout sidebar={<Sidebar sections={SIDEBAR_SECTIONS} />}>
      <Routes>
        <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
        <Route path={ROUTES.MEDICATIONS} element={<MedicationAdministration />} />
        <Route path={ROUTES.VITALS} element={<VitalSigns />} />
        <Route path={ROUTES.WARD} element={<WardManagement />} />
        <Route path={ROUTES.ADMISSIONS} element={<Admissions />} />
        <Route path={ROUTES.DISCHARGE} element={<Discharge />} />
        <Route path={ROUTES.BEDSIDE} element={<BedsideVerification />} />
        <Route path={ROUTES.BARCODE} element={<BarcodeScanning />} />
        <Route path={ROUTES.QR_VERIFICATION} element={<QRVerification />} />
        <Route path={ROUTES.OFFLINE} element={<OfflineMode />} />
        <Route path={ROUTES.CARE_PLAN} element={<CarePlan />} />
        <Route path={ROUTES.SHIFT_HANDOVER} element={<ShiftHandover />} />
        <Route path={ROUTES.TASKS} element={<TaskList />} />
        <Route path={ROUTES.PATIENT_ROUND} element={<PatientRound />} />
        <Route path={ROUTES.SETTINGS} element={<Settings />} />
        <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
      </Routes>
    </Layout>
  );
}

function AppRoutes() {
  const { isAuthenticated } = useNurse();
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path="*" element={<Navigate to={ROUTES.LOGIN} replace />} />
      </Routes>
    );
  }
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route path="/*" element={<ProtectedRoute isAuthenticated={isAuthenticated}><AppLayout /></ProtectedRoute>} />
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider defaultMode="light" defaultRtl>
      <BrowserRouter>
        <NurseProvider>
          <OfflineProvider>
            <AppRoutes />
          </OfflineProvider>
        </NurseProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
