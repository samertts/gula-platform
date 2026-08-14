import { createBrowserRouter, Navigate } from "react-router-dom";
import { lazy, Suspense, type ReactNode } from "react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { LoadingSpinner } from "@/components/shared/PageComponents";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { useAuth } from "@/contexts/AuthContext";
import type { UserRole } from "@/types";
import { LegacyRouteBridge } from "@/pages/migration/LegacyRouteBridge";

const LoginPage = lazy(() => import("@/pages/auth/LoginPage").then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/pages/auth/RegisterPage").then(m => ({ default: m.RegisterPage })));
const LegalPage = lazy(() => import("@/pages/legal/LegalPage").then(m => ({ default: m.LegalPage })));
const DashboardPage = lazy(() => import("@/pages/dashboard/DashboardPage").then(m => ({ default: m.DashboardPage })));
const PatientsPage = lazy(() => import("@/pages/patients/PatientsPage").then(m => ({ default: m.PatientsPage })));
const OrdersPage = lazy(() => import("@/pages/orders/OrdersPage").then(m => ({ default: m.OrdersPage })));
const ReportsPage = lazy(() => import("@/pages/reports/ReportsPage").then(m => ({ default: m.ReportsPage })));
const ResultsPage = lazy(() => import("@/pages/results/ResultsPage").then(m => ({ default: m.ResultsPage })));
const SamplesPage = lazy(() => import("@/pages/samples/SamplesPage").then(m => ({ default: m.SamplesPage })));
const LabsPage = lazy(() => import("@/pages/labs/LabsPage").then(m => ({ default: m.LabsPage })));
const CriticalAlertsPage = lazy(() => import("@/pages/alerts/CriticalAlertsPage").then(m => ({ default: m.CriticalAlertsPage })));
const NotificationsPage = lazy(() => import("@/pages/notifications/NotificationsPage").then(m => ({ default: m.NotificationsPage })));
const AIPage = lazy(() => import("@/pages/ai/AIPage").then(m => ({ default: m.AIPage })));
const AiPlatformPage = lazy(() => import("@/pages/ai-platform/AiPlatformPage").then(m => ({ default: m.AiPlatformPage })));
const StatsPage = lazy(() => import("@/pages/stats/StatsPage").then(m => ({ default: m.StatsPage })));
const QCPage = lazy(() => import("@/pages/qc/QCPage").then(m => ({ default: m.QCPage })));
const PatientCardPage = lazy(() => import("@/pages/patient-card/PatientCardPage").then(m => ({ default: m.PatientCardPage })));
const IdentityPage = lazy(() => import("@/pages/identity/IdentityPage").then(m => ({ default: m.IdentityPage })));
const TiersPage = lazy(() => import("@/pages/tiers/TiersPage").then(m => ({ default: m.TiersPage })));
const CompliancePage = lazy(() => import("@/pages/compliance/CompliancePage").then(m => ({ default: m.CompliancePage })));
const SettingsPage = lazy(() => import("@/pages/settings/SettingsPage").then(m => ({ default: m.SettingsPage })));
const ProfilePage = lazy(() => import("@/pages/profile/ProfilePage").then(m => ({ default: m.ProfilePage })));
const SecurityPage = lazy(() => import("@/pages/security/SecurityPage").then(m => ({ default: m.SecurityPage })));
const AdminLabsPage = lazy(() => import("@/pages/admin/AdminPages").then(m => ({ default: m.AdminLabsPage })));
const AdminUsersPage = lazy(() => import("@/pages/admin/AdminPages").then(m => ({ default: m.AdminUsersPage })));
const AdminAuditPage = lazy(() => import("@/pages/admin/AdminPages").then(m => ({ default: m.AdminAuditPage })));
const FhirPage = lazy(() => import("@/pages/fhir/FhirPage").then(m => ({ default: m.FhirPage })));
const HospitalPage = lazy(() => import("@/pages/hospital/HospitalPage").then(m => ({ default: m.HospitalPage })));
const EdgePage = lazy(() => import("@/pages/edge/EdgePage").then(m => ({ default: m.EdgePage })));
const FinancialPage = lazy(() => import("@/pages/financial/FinancialPage").then(m => ({ default: m.FinancialPage })));
const NationalDataPage = lazy(() => import("@/pages/national-data/NationalDataPage").then(m => ({ default: m.NationalDataPage })));
const NiamGovernancePage = lazy(() => import("@/pages/niam/GovernancePage"));
const NiamTrustPage = lazy(() => import("@/pages/niam/TrustPage"));
const NiamLifecyclePage = lazy(() => import("@/pages/niam/LifecyclePage"));
const NiamFederationPage = lazy(() => import("@/pages/niam/FederationPage"));
const NiamCertificatesPage = lazy(() => import("@/pages/niam/CertificatesPage"));
const NiamWorkflowsPage = lazy(() => import("@/pages/niam/WorkflowsPage"));
const NiamAdaptiveAuthPage = lazy(() => import("@/pages/niam/AdaptiveAuthPage"));
const AiFabricPageLazy = lazy(() => import("@/pages/ai-fabric/AiFabricPage"));
const BiomedicalApiPageLazy = lazy(() => import("@/pages/biomedical/BiomedicalApiPage"));
const BloodBankApiPageLazy = lazy(() => import("@/pages/blood-bank/BloodBankApiPage"));
const CapabilitiesClinicalFoundationPageLazy = lazy(() => import("@/pages/capabilities/clinical-foundation/CapabilitiesClinicalFoundationPage"));
const CapabilitiesDocumentManagementPageLazy = lazy(() => import("@/pages/capabilities/document-management/CapabilitiesDocumentManagementPage"));
const CapabilitiesEncounterManagementPageLazy = lazy(() => import("@/pages/capabilities/encounter-management/CapabilitiesEncounterManagementPage"));
const CapabilitiesHealthcareConsentPageLazy = lazy(() => import("@/pages/capabilities/healthcare-consent/CapabilitiesHealthcareConsentPage"));
const CapabilitiesProviderManagementPageLazy = lazy(() => import("@/pages/capabilities/provider-management/CapabilitiesProviderManagementPage"));
const CapabilitiesReportingServicePageLazy = lazy(() => import("@/pages/capabilities/reporting-service/CapabilitiesReportingServicePage"));
const CapabilitiesSearchServicePageLazy = lazy(() => import("@/pages/capabilities/search-service/CapabilitiesSearchServicePage"));
const CapabilitiesStorageServicePageLazy = lazy(() => import("@/pages/capabilities/storage-service/CapabilitiesStorageServicePage"));
const CapabilitiesWorkflowEnginePageLazy = lazy(() => import("@/pages/capabilities/workflow-engine/CapabilitiesWorkflowEnginePage"));
const CertificationPageLazy = lazy(() => import("@/pages/certification/CertificationPage"));
const CitizenPlatformPageLazy = lazy(() => import("@/pages/citizen-platform/CitizenPlatformPage"));
const CitizenWorkspacePageLazy = lazy(() => import("@/pages/citizen-platform/CitizenWorkspacePage"));
const CommandCenterApiPageLazy = lazy(() => import("@/pages/command-center/CommandCenterApiPage"));
const CommandIntelligencePageLazy = lazy(() => import("@/pages/command-intelligence/CommandIntelligencePage"));
const ControlPlanePageLazy = lazy(() => import("@/pages/control-plane/ControlPlanePage"));
const CriticalCareApiPageLazy = lazy(() => import("@/pages/critical-care/CriticalCareApiPage"));
const EmsApiPageLazy = lazy(() => import("@/pages/ems/EmsApiPage"));
const HealthDataPageLazy = lazy(() => import("@/pages/health-data/HealthDataPage"));
const IntegrationPageLazy = lazy(() => import("@/pages/integration/IntegrationPage"));
const IntegrationConnectorsPageLazy = lazy(() => import("@/pages/integration/connectors/IntegrationConnectorsPage"));
const KernelPageLazy = lazy(() => import("@/pages/kernel/KernelPage"));
const LifecyclePlatformApiPageLazy = lazy(() => import("@/pages/lifecycle-platform/LifecyclePlatformApiPage"));
const NationalBackgroundPlatformApiPageLazy = lazy(() => import("@/pages/national/background-platform/NationalBackgroundPlatformApiPage"));
const NationalDocumentPlatformApiPageLazy = lazy(() => import("@/pages/national/document-platform/NationalDocumentPlatformApiPage"));
const NationalEcosystemPageLazy = lazy(() => import("@/pages/national/ecosystem/NationalEcosystemPage"));
const NationalEcosystemGatewayPageLazy = lazy(() => import("@/pages/national/ecosystem/gateway/NationalEcosystemGatewayPage"));
const NationalNotificationPlatformApiPageLazy = lazy(() => import("@/pages/national/notification-platform/NationalNotificationPlatformApiPage"));
const NationalObservabilityApiPageLazy = lazy(() => import("@/pages/national/observability/NationalObservabilityApiPage"));
const NationalRulesEngineApiPageLazy = lazy(() => import("@/pages/national/rules-engine/NationalRulesEngineApiPage"));
const NationalSchedulingPlatformApiPageLazy = lazy(() => import("@/pages/national/scheduling-platform/NationalSchedulingPlatformApiPage"));
const NationalSearchPlatformApiPageLazy = lazy(() => import("@/pages/national/search-platform/NationalSearchPlatformApiPage"));
const NationalTaskEngineApiPageLazy = lazy(() => import("@/pages/national/task-engine/NationalTaskEngineApiPage"));
const NationalWorkflowRuntimeApiPageLazy = lazy(() => import("@/pages/national/workflow-runtime/NationalWorkflowRuntimeApiPage"));
const PharmacyPageLazy = lazy(() => import("@/pages/pharmacy/PharmacyPage"));
const PilotPlatformApiPageLazy = lazy(() => import("@/pages/pilot-platform/PilotPlatformApiPage"));
const PlatformPageLazy = lazy(() => import("@/pages/platform/PlatformPage"));
const PublicHealthApiPageLazy = lazy(() => import("@/pages/public-health/PublicHealthApiPage"));

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function LazyPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<LoadingSpinner />}>{children}</Suspense>;
}

const adminRoles: UserRole[] = ['master_admin', 'admin', 'lab_admin', 'ministry_admin', 'province_admin'];
const staffRoles: UserRole[] = ['master_admin', 'admin', 'lab_admin', 'doctor', 'staff', 'lab_staff', 'technician'];
const readonlyRoles: UserRole[] = ['master_admin', 'admin', 'lab_admin', 'doctor', 'staff', 'lab_staff', 'demo_viewer'];
const labRoles: UserRole[] = ['master_admin', 'admin', 'lab_admin', 'staff', 'lab_staff'];

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AuthLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: "login", element: <LazyPage><LoginPage /></LazyPage> },
      { path: "register", element: <LazyPage><RegisterPage /></LazyPage> },
      { path: "privacy-policy", element: <LazyPage><LegalPage document="privacy" /></LazyPage> },
      { path: "terms-of-service", element: <LazyPage><LegalPage document="terms" /></LazyPage> },
    ],
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <LazyPage><DashboardPage /></LazyPage> },
      { path: "patients", element: <RoleGuard roles={staffRoles}><LazyPage><PatientsPage /></LazyPage></RoleGuard> },
      { path: "orders", element: <RoleGuard roles={staffRoles}><LazyPage><OrdersPage /></LazyPage></RoleGuard> },
      { path: "reports", element: <RoleGuard roles={readonlyRoles}><LazyPage><ReportsPage /></LazyPage></RoleGuard> },
      { path: "results", element: <RoleGuard roles={staffRoles}><LazyPage><ResultsPage /></LazyPage></RoleGuard> },
      { path: "samples", element: <RoleGuard roles={labRoles}><LazyPage><SamplesPage /></LazyPage></RoleGuard> },
      { path: "labs", element: <RoleGuard roles={readonlyRoles}><LazyPage><LabsPage /></LazyPage></RoleGuard> },
      { path: "alerts", element: <RoleGuard roles={readonlyRoles}><LazyPage><CriticalAlertsPage /></LazyPage></RoleGuard> },
      { path: "notifications", element: <LazyPage><NotificationsPage /></LazyPage> },
      { path: "ai", element: <RoleGuard roles={readonlyRoles}><LazyPage><AIPage /></LazyPage></RoleGuard> },
      { path: "ai-platform", element: <RoleGuard roles={readonlyRoles}><LazyPage><AiPlatformPage /></LazyPage></RoleGuard> },
      { path: "stats", element: <RoleGuard roles={readonlyRoles}><LazyPage><StatsPage /></LazyPage></RoleGuard> },
      { path: "qc", element: <RoleGuard roles={readonlyRoles}><LazyPage><QCPage /></LazyPage></RoleGuard> },
      { path: "patient-card", element: <RoleGuard roles={staffRoles}><LazyPage><PatientCardPage /></LazyPage></RoleGuard> },
      { path: "identity", element: <RoleGuard roles={staffRoles}><LazyPage><IdentityPage /></LazyPage></RoleGuard> },
      { path: "tiers", element: <RoleGuard roles={readonlyRoles}><LazyPage><TiersPage /></LazyPage></RoleGuard> },
      { path: "compliance", element: <RoleGuard roles={adminRoles}><LazyPage><CompliancePage /></LazyPage></RoleGuard> },
      { path: "settings", element: <LazyPage><SettingsPage /></LazyPage> },
      { path: "profile", element: <LazyPage><ProfilePage /></LazyPage> },
      { path: "security", element: <RoleGuard roles={adminRoles}><LazyPage><SecurityPage /></LazyPage></RoleGuard> },
      { path: "admin/labs", element: <RoleGuard roles={adminRoles}><LazyPage><AdminLabsPage /></LazyPage></RoleGuard> },
      { path: "admin/users", element: <RoleGuard roles={adminRoles}><LazyPage><AdminUsersPage /></LazyPage></RoleGuard> },
      { path: "admin/audit", element: <RoleGuard roles={adminRoles}><LazyPage><AdminAuditPage /></LazyPage></RoleGuard> },
      { path: "fhir", element: <RoleGuard roles={adminRoles}><LazyPage><FhirPage /></LazyPage></RoleGuard> },
      { path: "ehr", element: <RoleGuard roles={adminRoles}><LegacyRouteBridge /></RoleGuard> },
      { path: "hospital", element: <RoleGuard roles={adminRoles}><LazyPage><HospitalPage /></LazyPage></RoleGuard> },
      { path: "edge", element: <RoleGuard roles={['master_admin', 'admin']}><LazyPage><EdgePage /></LazyPage></RoleGuard> },
      { path: "financial", element: <RoleGuard roles={adminRoles}><LazyPage><FinancialPage /></LazyPage></RoleGuard> },
      { path: "national-data", element: <RoleGuard roles={['master_admin', 'ministry_admin', 'province_admin']}><LazyPage><NationalDataPage /></LazyPage></RoleGuard> },
      { path: "niam/governance", element: <RoleGuard roles={adminRoles}><LazyPage><NiamGovernancePage /></LazyPage></RoleGuard> },
      { path: "niam/trust", element: <RoleGuard roles={adminRoles}><LazyPage><NiamTrustPage /></LazyPage></RoleGuard> },
      { path: "niam/lifecycle", element: <RoleGuard roles={adminRoles}><LazyPage><NiamLifecyclePage /></LazyPage></RoleGuard> },
      { path: "niam/federation", element: <RoleGuard roles={adminRoles}><LazyPage><NiamFederationPage /></LazyPage></RoleGuard> },
      { path: "niam/certificates", element: <RoleGuard roles={adminRoles}><LazyPage><NiamCertificatesPage /></LazyPage></RoleGuard> },
      { path: "niam/workflows", element: <RoleGuard roles={adminRoles}><LazyPage><NiamWorkflowsPage /></LazyPage></RoleGuard> },
      { path: "niam/adaptive-auth", element: <RoleGuard roles={adminRoles}><LazyPage><NiamAdaptiveAuthPage /></LazyPage></RoleGuard> },
      { path: "ai-fabric", element: <RoleGuard roles={adminRoles}><LazyPage><AiFabricPageLazy /></LazyPage></RoleGuard> },
      { path: "biomedical", element: <RoleGuard roles={adminRoles}><LazyPage><BiomedicalApiPageLazy /></LazyPage></RoleGuard> },
      { path: "blood-bank", element: <RoleGuard roles={adminRoles}><LazyPage><BloodBankApiPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/clinical-foundation", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesClinicalFoundationPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/document-management", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesDocumentManagementPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/encounter-management", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesEncounterManagementPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/healthcare-consent", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesHealthcareConsentPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/provider-management", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesProviderManagementPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/reporting-service", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesReportingServicePageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/search-service", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesSearchServicePageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/storage-service", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesStorageServicePageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/workflow-engine", element: <RoleGuard roles={readonlyRoles}><LazyPage><CapabilitiesWorkflowEnginePageLazy /></LazyPage></RoleGuard> },
      { path: "certification", element: <RoleGuard roles={adminRoles}><LazyPage><CertificationPageLazy /></LazyPage></RoleGuard> },
      { path: "citizen", element: <RoleGuard roles={["citizen"]}><LazyPage><CitizenWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "citizen-platform", element: <RoleGuard roles={adminRoles}><LazyPage><CitizenPlatformPageLazy /></LazyPage></RoleGuard> },
      { path: "command-center", element: <RoleGuard roles={adminRoles}><LazyPage><CommandCenterApiPageLazy /></LazyPage></RoleGuard> },
      { path: "command-intelligence", element: <RoleGuard roles={adminRoles}><LazyPage><CommandIntelligencePageLazy /></LazyPage></RoleGuard> },
      { path: "control-plane", element: <RoleGuard roles={adminRoles}><LazyPage><ControlPlanePageLazy /></LazyPage></RoleGuard> },
      { path: "critical-care", element: <RoleGuard roles={adminRoles}><LazyPage><CriticalCareApiPageLazy /></LazyPage></RoleGuard> },
      { path: "ems", element: <RoleGuard roles={adminRoles}><LazyPage><EmsApiPageLazy /></LazyPage></RoleGuard> },
      { path: "health-data", element: <RoleGuard roles={adminRoles}><LazyPage><HealthDataPageLazy /></LazyPage></RoleGuard> },
      { path: "integration", element: <RoleGuard roles={adminRoles}><LazyPage><IntegrationPageLazy /></LazyPage></RoleGuard> },
      { path: "integration/connectors", element: <RoleGuard roles={adminRoles}><LazyPage><IntegrationConnectorsPageLazy /></LazyPage></RoleGuard> },
      { path: "kernel", element: <RoleGuard roles={adminRoles}><LazyPage><KernelPageLazy /></LazyPage></RoleGuard> },
      { path: "lifecycle-platform", element: <RoleGuard roles={adminRoles}><LazyPage><LifecyclePlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/background-platform", element: <RoleGuard roles={adminRoles}><LazyPage><NationalBackgroundPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/document-platform", element: <RoleGuard roles={adminRoles}><LazyPage><NationalDocumentPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/ecosystem", element: <RoleGuard roles={adminRoles}><LazyPage><NationalEcosystemPageLazy /></LazyPage></RoleGuard> },
      { path: "national/ecosystem/gateway", element: <RoleGuard roles={adminRoles}><LazyPage><NationalEcosystemGatewayPageLazy /></LazyPage></RoleGuard> },
      { path: "national/notification-platform", element: <RoleGuard roles={adminRoles}><LazyPage><NationalNotificationPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/observability", element: <RoleGuard roles={adminRoles}><LazyPage><NationalObservabilityApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/rules-engine", element: <RoleGuard roles={adminRoles}><LazyPage><NationalRulesEngineApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/scheduling-platform", element: <RoleGuard roles={adminRoles}><LazyPage><NationalSchedulingPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/search-platform", element: <RoleGuard roles={adminRoles}><LazyPage><NationalSearchPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/task-engine", element: <RoleGuard roles={adminRoles}><LazyPage><NationalTaskEngineApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/workflow-runtime", element: <RoleGuard roles={adminRoles}><LazyPage><NationalWorkflowRuntimeApiPageLazy /></LazyPage></RoleGuard> },
      { path: "pharmacy", element: <RoleGuard roles={adminRoles}><LazyPage><PharmacyPageLazy /></LazyPage></RoleGuard> },
      { path: "pilot-platform", element: <RoleGuard roles={adminRoles}><LazyPage><PilotPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "platform", element: <RoleGuard roles={adminRoles}><LazyPage><PlatformPageLazy /></LazyPage></RoleGuard> },
      { path: "public-health", element: <RoleGuard roles={adminRoles}><LazyPage><PublicHealthApiPageLazy /></LazyPage></RoleGuard> },
      { path: "admin", element: <Navigate to="/admin/labs" replace /> },
      { path: "*", element: <LegacyRouteBridge /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
