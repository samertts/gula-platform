import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { lazy, useState } from 'react';
function lazyNamed<T extends Record<string, React.ComponentType<any>>, N extends string>(load: () => Promise<T>, name: N) {
  return lazy(() => load().then(m => ({ default: m[name]! })));
}
const DashboardView = lazyNamed(() => import('./views/DashboardView'), 'DashboardView');
const RecordsView = lazyNamed(() => import('./views/RecordsView'), 'RecordsView');
const AppointmentsView = lazyNamed(() => import('./views/AppointmentsView'), 'AppointmentsView');
const SettingsView = lazyNamed(() => import('./views/SettingsView'), 'SettingsView');
const LandingAuthView = lazyNamed(() => import('./views/LandingAuthView'), 'LandingAuthView');
const LabDashboard = lazyNamed(() => import('./views/lab/LabDashboard'), 'LabDashboard');
const WorkQueue = lazyNamed(() => import('./views/lab/WorkQueue'), 'WorkQueue');
const DeviceMonitoring = lazyNamed(() => import('./views/lab/DeviceMonitoring'), 'DeviceMonitoring');
const InventoryManagement = lazyNamed(() => import('./views/lab/InventoryManagement'), 'InventoryManagement');
const SampleTracking = lazyNamed(() => import('./views/lab/SampleTracking'), 'SampleTracking');
const QualityControl = lazyNamed(() => import('./views/lab/QualityControl'), 'QualityControl');
const DoctorIntelligence = lazyNamed(() => import('./views/doctor/DoctorIntelligence'), 'DoctorIntelligence');
const PatientProfile = lazyNamed(() => import('./views/doctor/PatientProfile'), 'PatientProfile');
const ImagingLabView = lazyNamed(() => import('./views/ImagingLabView'), 'ImagingLabView');
const CitizenHealth = lazyNamed(() => import('./views/citizen/CitizenHealth'), 'CitizenHealth');
const PatientRegistration = lazyNamed(() => import('./views/citizen/PatientRegistration'), 'PatientRegistration');
const IdentityVerificationView = lazyNamed(() => import('./views/citizen/IdentityVerificationView'), 'IdentityVerificationView');
const ConsentManagementView = lazyNamed(() => import('./views/citizen/ConsentManagementView'), 'ConsentManagementView');
const MedicalHistoryView = lazyNamed(() => import('./views/citizen/MedicalHistoryView'), 'MedicalHistoryView');
const AuditLog = lazyNamed(() => import('./views/admin/AuditLog'), 'AuditLog');
const InfrastructureView = lazyNamed(() => import('./views/admin/InfrastructureView'), 'InfrastructureView');
const IntegrationHub = lazyNamed(() => import('./views/admin/IntegrationHub'), 'IntegrationHub');
const SystemsArchitectureView = lazyNamed(() => import('./views/admin/SystemsArchitectureView'), 'SystemsArchitectureView');
const ResearcherDashboard = lazyNamed(() => import('./views/research/ResearcherDashboard'), 'ResearcherDashboard');
const CitizenDashboard = lazyNamed(() => import('./views/citizen/CitizenDashboard'), 'CitizenDashboard');
const SmartResultsView = lazyNamed(() => import('./views/citizen/SmartResultsView'), 'SmartResultsView');
const CitizenAssistant = lazyNamed(() => import('./views/citizen/CitizenAssistant'), 'CitizenAssistant');
const FamilyManagement = lazyNamed(() => import('./views/citizen/FamilyManagement'), 'FamilyManagement');
const MedicationCenter = lazyNamed(() => import('./views/citizen/MedicationCenter'), 'MedicationCenter');
const NationalHealthGrid = lazyNamed(() => import('./views/ministry/NationalHealthGrid'), 'NationalHealthGrid');
const EpidemiologicalIntelligence = lazyNamed(() => import('./views/ministry/EpidemiologicalIntelligence'), 'EpidemiologicalIntelligence');
const DataSovereigntyAudit = lazyNamed(() => import('./views/ministry/DataSovereigntyAudit'), 'DataSovereigntyAudit');
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PermissionGuard } from './components/PermissionGuard';
import { Toaster } from 'sonner';
import { CommandPalette } from './components/CommandPalette';
import { HelpAssistant } from './components/HelpAssistant';
import { GlobalAiAssistant } from './components/GlobalAiAssistant';
import { ShortcutsModal } from './components/ShortcutsModal';
import { RouteErrorBoundary } from './components/ui/ErrorBoundary';
import { useKeySequence } from './lib/useShortcut';
import {WifiOff} from 'lucide-react';
import { useEffect, Suspense } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { NavigationProvider } from './stores/navigationStore';
import { WorkspaceProvider } from './stores/workspaceStore';
export default function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <NotificationProvider>
          <NavigationProvider>
            <WorkspaceProvider>
              <Toaster position="top-right" richColors />
              <AppContent />
            </WorkspaceProvider>
          </NavigationProvider>
        </NotificationProvider>
      </LanguageProvider>
    </AuthProvider>
  );
}
import { Breadcrumbs } from './components/Breadcrumbs';
import { ScrollToTop } from './components/ScrollToTop';
function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <RouteErrorBoundary resetKey={location.pathname}>
      <Suspense fallback={
        <div className="flex items-center justify-center h-screen">
          <div className="flex flex-col items-center gap-4">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest animate-pulse">Loading...</span>
          </div>
        </div>
      }>
      <Routes location={location} key={location.pathname}>
        {/* Doctor Wing */}
        <Route path="/" element={<DashboardView />} />
        <Route path="/patients" element={<RecordsView />} />
        <Route path="/patients/:id" element={<PatientProfile />} />
        <Route path="/appointments" element={<AppointmentsView />} />
        <Route path="/intelligence" element={<DoctorIntelligence />} />
        {/* Lab Wing */}
        <Route path="/lab/dashboard" element={<LabDashboard />} />
        <Route path="/lab/queue" element={<WorkQueue />} />
        <Route path="/lab/devices" element={<DeviceMonitoring />} />
        <Route path="/lab/inventory" element={<InventoryManagement />} />
        <Route path="/lab/samples" element={<SampleTracking />} />
        <Route path="/lab/qc" element={<QualityControl />} />
        <Route path="/lab/imaging" element={<ImagingLabView />} />
        {/* Citizen Wing */}
        <Route path="/citizen/dashboard" element={<CitizenDashboard />} />
        <Route path="/citizen/profile" element={<CitizenHealth />} />
        <Route path="/citizen/assistant" element={<CitizenAssistant />} />
        <Route path="/citizen/medications" element={<MedicationCenter />} />
        <Route path="/citizen/appointments" element={<AppointmentsView />} />
        <Route path="/citizen/family" element={<FamilyManagement />} />
        <Route path="/citizen/results" element={<SmartResultsView />} />
        <Route path="/citizen/history" element={<MedicalHistoryView />} />
        <Route path="/citizen/security" element={<AuditLog />} />
        <Route path="/citizen/verification" element={<IdentityVerificationView />} />
        <Route path="/citizen/consent" element={<ConsentManagementView />} />
        <Route path="/citizen/register" element={<PatientRegistration />} />
        {/* Admin Wing */}
        <Route path="/admin/audit" element={
          <PermissionGuard resource="audit_log" action="read"><AuditLog /></PermissionGuard>
        } />
        <Route path="/admin/infrastructure" element={
          <PermissionGuard resource="infrastructure" action="read"><InfrastructureView /></PermissionGuard>
        } />
        <Route path="/admin/architecture" element={
          <PermissionGuard resource="architecture" action="read"><SystemsArchitectureView /></PermissionGuard>
        } />
        <Route path="/admin/integrations" element={
          <PermissionGuard resource="integration" action="read"><IntegrationHub /></PermissionGuard>
        } />
        {/* Ministry Wing */}
        <Route path="/ministry/dashboard" element={
          <PermissionGuard resource="patient" action="read" scope="global"><NationalHealthGrid /></PermissionGuard>
        } />
        <Route path="/ministry/epidemiology" element={
          <PermissionGuard resource="patient" action="read" scope="global"><EpidemiologicalIntelligence /></PermissionGuard>
        } />
        <Route path="/ministry/audit" element={
          <PermissionGuard resource="patient" action="manage" scope="global"><DataSovereigntyAudit /></PermissionGuard>
        } />
        <Route path="/ministry/analytics" element={
          <PermissionGuard resource="research" action="read"><ResearcherDashboard /></PermissionGuard>
        } />
        {/* Shared */}
        <Route path="/settings" element={<SettingsView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </Suspense>
      </RouteErrorBoundary>
    </AnimatePresence>
  );
}
function GlobalShortcuts({ onOpenShortcuts }: { onOpenShortcuts: () => void }) {
  const navigate = useNavigate();
  useKeySequence({
    'g d': () => navigate('/'),
    'g p': () => navigate('/patients'),
    'g a': () => navigate('/appointments'),
    'g i': () => navigate('/intelligence'),
    'g l': () => navigate('/lab/dashboard'),
    'g q': () => navigate('/lab/queue'),
    'g s': () => navigate('/settings'),
    'g h': () => onOpenShortcuts(),
  });
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
      const t = e.target as HTMLElement | null;
      if (!t) return;
      if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable) return;
      e.preventDefault();
      window.dispatchEvent(new CustomEvent('open-command-palette'));
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
  return null;
}
function AppContent() {
  const { user, isLoading } = useAuth();
  const { t, isRtl } = useLanguage();
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  useEffect(() => {
    const handler = (e: CustomEvent) => setSidebarExpanded(e.detail);
    window.addEventListener('sidebar-expanded' as any, handler as any);
    return () => window.removeEventListener('sidebar-expanded' as any, handler as any);
  }, []);
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tgt = e.target as HTMLElement | null;
      const inEditable = !!tgt && (['INPUT', 'TEXTAREA', 'SELECT'].includes(tgt.tagName) || tgt.isContentEditable);
      if (e.key === '?' && !inEditable) setShowShortcuts(prev => !prev);
      if (e.key === 'Escape') setShowShortcuts(false);
    };
    const handleOpenShortcuts = () => setShowShortcuts(true);
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('open-shortcuts', handleOpenShortcuts);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('open-shortcuts', handleOpenShortcuts);
    };
  }, []);
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest animate-pulse">Initializing secure session...</span>
        </div>
      </div>
    );
  }
  if (!user) {
    return <LandingAuthView />;
  }
  const sidebarWidth = sidebarExpanded ? (isRtl ? 'lg:mr-64' : 'lg:ml-64') : (isRtl ? 'lg:mr-16' : 'lg:ml-16');
  return (
    <BrowserRouter>
      <GlobalShortcuts onOpenShortcuts={() => setShowShortcuts(true)} />
      <CommandPalette />
      <HelpAssistant />
      <GlobalAiAssistant />
      <ShortcutsModal isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
      <ScrollToTop />
      <div className="flex min-h-screen bg-slate-50 font-sans antialiased selection:bg-indigo-100/50 transition-colors duration-500" dir={isRtl ? 'rtl' : 'ltr'}>
        <Sidebar />
        <main className={`flex-1 flex flex-col h-screen overflow-hidden ${sidebarWidth}`}>
          <TopBar />
          {/* Offline indicator */}
          <AnimatePresence>
            {isOffline && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-amber-50 border-b border-amber-100"
              >
                <div className="max-w-screen-2xl mx-auto px-4 md:px-6 py-2 flex items-center gap-3">
                  <div className="w-7 h-7 bg-amber-500 rounded-lg flex items-center justify-center">
                    <WifiOff size={14} className="text-white" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[11px] font-bold text-amber-800">{t.offlineMode || 'Offline Mode'}</span>
                    <span className="text-[9px] text-amber-600">{t.localQueue || 'Changes will sync when connection resumes'}</span>
                  </div>
                  <div className="ml-auto flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse" />
                    <span className="text-[9px] font-bold text-amber-700 uppercase tracking-wider">Offline</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div className="flex-1 overflow-y-auto bg-slate-50 custom-scrollbar">
            <div className="max-w-[1600px] mx-auto px-4 md:px-8 pt-8 pb-12">
              <Breadcrumbs />
              <AnimatedRoutes />
            </div>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}