import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { DashboardView } from './views/DashboardView';
import { RecordsView } from './views/RecordsView';
import { AppointmentsView } from './views/AppointmentsView';
import { LabResultsView } from './views/LabResultsView';
import { SettingsView } from './views/SettingsView';
import { LandingAuthView } from './views/LandingAuthView';
import { LabDashboard } from './views/lab/LabDashboard';
import { WorkQueue } from './views/lab/WorkQueue';
import { DeviceMonitoring } from './views/lab/DeviceMonitoring';
import { InventoryManagement } from './views/lab/InventoryManagement';
import { SampleTracking } from './views/lab/SampleTracking';
import { QualityControl } from './views/lab/QualityControl';
import { DoctorIntelligence } from './views/doctor/DoctorIntelligence';
import { PatientProfile } from './views/doctor/PatientProfile';
import { ImagingLabView } from './views/ImagingLabView';
import { CitizenHealth } from './views/citizen/CitizenHealth';
import { PatientRegistration } from './views/citizen/PatientRegistration';
import { IdentityVerificationView } from './views/citizen/IdentityVerificationView';
import { ConsentManagementView } from './views/citizen/ConsentManagementView';
import { MedicalHistoryView } from './views/citizen/MedicalHistoryView';
import { AuditLog } from './views/admin/AuditLog';
import { InfrastructureView } from './views/admin/InfrastructureView';
import { IntegrationHub } from './views/admin/IntegrationHub';
import { SystemsArchitectureView } from './views/admin/SystemsArchitectureView';
import { ResearcherDashboard } from './views/research/ResearcherDashboard';
import { CitizenDashboard } from './views/citizen/CitizenDashboard';
import { SmartResultsView } from './views/citizen/SmartResultsView';
import { CitizenAssistant } from './views/citizen/CitizenAssistant';
import { FamilyManagement } from './views/citizen/FamilyManagement';
import { MedicationCenter } from './views/citizen/MedicationCenter';
import { NationalHealthGrid } from './views/ministry/NationalHealthGrid';
import { EpidemiologicalIntelligence } from './views/ministry/EpidemiologicalIntelligence';
import { DataSovereigntyAudit } from './views/ministry/DataSovereigntyAudit';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PermissionGuard } from './components/PermissionGuard';
import { Toaster } from 'sonner';
import { CommandPalette } from './components/CommandPalette';
import { HelpAssistant } from './components/HelpAssistant';
import { GlobalAiAssistant } from './components/GlobalAiAssistant';
import { ShortcutsModal } from './components/ShortcutsModal';
import { WifiOff, Activity as ActivityIcon } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';

export default function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <NotificationProvider>
          <Toaster position="top-right" richColors />
          <AppContent />
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
          <PermissionGuard resource="audit_log" action="read">
            <AuditLog />
          </PermissionGuard>
        } />
        <Route path="/admin/infrastructure" element={
          <PermissionGuard resource="infrastructure" action="read">
            <InfrastructureView />
          </PermissionGuard>
        } />
        <Route path="/admin/architecture" element={
          <PermissionGuard resource="architecture" action="read">
            <SystemsArchitectureView />
          </PermissionGuard>
        } />
        <Route path="/admin/integrations" element={
          <PermissionGuard resource="integration" action="read">
            <IntegrationHub />
          </PermissionGuard>
        } />

        {/* Ministry Wing */}
        <Route path="/ministry/dashboard" element={
          <PermissionGuard resource="patient" action="read" scope="global">
            <NationalHealthGrid />
          </PermissionGuard>
        } />
        <Route path="/ministry/epidemiology" element={
          <PermissionGuard resource="patient" action="read" scope="global">
            <EpidemiologicalIntelligence />
          </PermissionGuard>
        } />
        <Route path="/ministry/audit" element={
          <PermissionGuard resource="patient" action="manage" scope="global">
            <DataSovereigntyAudit />
          </PermissionGuard>
        } />
        <Route path="/ministry/analytics" element={
          <PermissionGuard resource="research" action="read">
            <ResearcherDashboard />
          </PermissionGuard>
        } />
        
        {/* Shared */}
        <Route path="/settings" element={<SettingsView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

function AppContent() {
  const { user, isLoading } = useAuth();
  const { t } = useLanguage();
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [showShortcuts, setShowShortcuts] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
        setShowShortcuts(prev => !prev);
      }
      if (e.key === 'Escape') {
        setShowShortcuts(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
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
        <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <LandingAuthView />;
  }

  return (
    <BrowserRouter>
      <CommandPalette />
      <HelpAssistant />
      <GlobalAiAssistant />
      <ShortcutsModal isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
      <ScrollToTop />
      <div className="flex min-h-screen bg-slate-50 font-sans antialiased selection:bg-indigo-100/50 transition-colors duration-500">
      <Sidebar />

      <main className="lg:ml-72 flex-1 flex flex-col h-screen overflow-hidden rtl:lg:ml-0 rtl:lg:mr-72">
        <TopBar />
        
        <AnimatePresence>
          {isOffline && (
            <motion.div 
              initial={{ opacity: 0, x: -50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: -50, scale: 0.9 }}
              className="fixed bottom-8 left-8 z-[60] flex items-center gap-4 bg-slate-900/90 text-white px-5 py-3 rounded-[2rem] shadow-2xl border border-white/10 backdrop-blur-xl pointer-events-none"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-amber-500 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/20">
                  <WifiOff size={18} className="animate-pulse" />
                </div>
                <div className="flex flex-col">
                  <p className="text-[10px] font-black uppercase tracking-widest leading-none mb-1">{t.offlineMode}</p>
                  <div className="flex items-center gap-1.5 opacity-60">
                    <ActivityIcon size={10} className="text-amber-400" />
                    <span className="text-[8px] font-bold uppercase tracking-[0.15em]">{t.localQueue}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex-1 overflow-y-auto bg-slate-50 custom-scrollbar">
          <div className="max-w-[1600px] mx-auto px-4 md:px-10 pt-10">
            <Breadcrumbs />
          </div>
          <AnimatedRoutes />
        </div>
      </main>
    </div>
    </BrowserRouter>
  );
}
