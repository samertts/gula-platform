import { createBrowserRouter, Navigate } from "react-router-dom";
import { lazy, Suspense, type ReactNode } from "react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { LoadingSpinner, PageLoadingSkeleton } from "@/components/shared/PageComponents";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { useAuth } from "@/contexts/AuthContext";
import {
  ADMIN_ROLES,
  FINANCIAL_ROLES,
  LAB_ROLES,
  PHARMACY_OPERATIONS_ROLES,
  RADIOLOGY_OPERATIONS_ROLES,
  CLINIC_OPERATIONS_ROLES,
  HOSPITAL_OPERATIONS_ROLES,
  ACUTE_CARE_OPERATIONS_ROLES,
  READONLY_ROLES,
  STAFF_ROLES,
  ROUTE_ROLE_POLICIES,
} from "@/permissions/routePolicies";
import { LegacyRouteBridge } from "@/pages/migration/LegacyRouteBridge";

const LoginPage = lazy(() => import("@/pages/auth/LoginPage").then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/pages/auth/RegisterPage").then(m => ({ default: m.RegisterPage })));
const LegalPage = lazy(() => import("@/pages/legal/LegalPage").then(m => ({ default: m.LegalPage })));
const DashboardPage = lazy(() => import("@/pages/dashboard/DashboardPage").then(m => ({ default: m.DashboardPage })));
const PatientsPage = lazy(() => import("@/pages/patients/PatientsPage").then(m => ({ default: m.PatientsPage })));
const PatientManagementWorkspacePageLazy = lazy(() => import("@/pages/patients/PatientManagementWorkspacePage"));
const OrganizationWorkspacePageLazy = lazy(() => import("@/pages/organization/OrganizationWorkspacePage"));
const LabOperationsWorkspacePageLazy = lazy(() => import("@/pages/lab/LabOperationsWorkspacePage"));
const RadiologyOperationsWorkspacePageLazy = lazy(() => import("@/pages/radiology/RadiologyOperationsWorkspacePage"));
const ClinicOperationsWorkspacePageLazy = lazy(() => import("@/pages/clinic/ClinicOperationsWorkspacePage"));
const HospitalOperationsWorkspacePageLazy = lazy(() => import("@/pages/hospital/HospitalOperationsWorkspacePage"));
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
const PatientVisitReadinessPage = lazy(() => import("@/pages/patient-visit/PatientVisitReadinessPage").then(m => ({ default: m.PatientVisitReadinessPage })));
const IdentityPage = lazy(() => import("@/pages/identity/IdentityPage").then(m => ({ default: m.IdentityPage })));
const TiersPage = lazy(() => import("@/pages/tiers/TiersPage").then(m => ({ default: m.TiersPage })));
const CompliancePage = lazy(() => import("@/pages/compliance/CompliancePage").then(m => ({ default: m.CompliancePage })));
const SettingsPage = lazy(() => import("@/pages/settings/SettingsPage").then(m => ({ default: m.SettingsPage })));
const AccessibilityCenterPage = lazy(() => import("@/pages/settings/AccessibilityCenterPage").then(m => ({ default: m.AccessibilityCenterPage })));
const ProfilePage = lazy(() => import("@/pages/profile/ProfilePage").then(m => ({ default: m.ProfilePage })));
const SecurityPage = lazy(() => import("@/pages/security/SecurityPage").then(m => ({ default: m.SecurityPage })));
const AdminLabsPage = lazy(() => import("@/pages/admin/AdminPages").then(m => ({ default: m.AdminLabsPage })));
const AdminUsersPage = lazy(() => import("@/pages/admin/AdminPages").then(m => ({ default: m.AdminUsersPage })));
const AdminAuditPage = lazy(() => import("@/pages/admin/AdminPages").then(m => ({ default: m.AdminAuditPage })));
const FhirPage = lazy(() => import("@/pages/fhir/FhirPage").then(m => ({ default: m.FhirPage })));
const EdgePage = lazy(() => import("@/pages/edge/EdgePage").then(m => ({ default: m.EdgePage })));
const FinancialPage = lazy(() => import("@/pages/financial/FinancialPage").then(m => ({ default: m.FinancialPage })));
const FinancialGovernancePage = lazy(() => import("@/pages/financial-governance/FinancialGovernancePage").then(m => ({ default: m.FinancialGovernancePage })));
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
const MyRecordPageLazy = lazy(() => import("@/pages/my-record/MyRecordPage"));
const CommandCenterApiPageLazy = lazy(() => import("@/pages/command-center/CommandCenterApiPage"));
const CommandIntelligencePageLazy = lazy(() => import("@/pages/command-intelligence/CommandIntelligencePage"));
const ControlPlanePageLazy = lazy(() => import("@/pages/control-plane/ControlPlanePage"));
const AcuteCareOperationsWorkspacePageLazy = lazy(() => import("@/pages/acute-care/AcuteCareOperationsWorkspacePage"));
const ScreenByScreenPageLazy = lazy(() => import("@/pages/screen-by-screen/ScreenByScreenPage"));
const HealthDataPageLazy = lazy(() => import("@/pages/health-data/HealthDataPage"));
const IntegrationPageLazy = lazy(() => import("@/pages/integration/IntegrationPage"));
const IntegrationConnectorsPageLazy = lazy(() => import("@/pages/integration/connectors/IntegrationConnectorsPage"));
const HealthEcosystemPageLazy = lazy(() => import("@/pages/integration/HealthEcosystemPage"));
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
const PharmacyOperationsWorkspacePageLazy = lazy(() => import("@/pages/pharmacy/PharmacyOperationsWorkspacePage"));
const BillingInsuranceWorkspacePageLazy = lazy(() => import("@/pages/billing/BillingInsuranceWorkspacePage"));
const DeviceIntegrationWorkspacePageLazy = lazy(() => import("@/pages/devices/DeviceIntegrationWorkspacePage").then(m => ({ default: m.DeviceIntegrationWorkspacePage })));
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
  return <Suspense fallback={<PageLoadingSkeleton />}>{children}</Suspense>;
}

function InstitutionalOnlyRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <LoadingSpinner />;
  if (!user?.lab_id || user.role === "citizen") return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}


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
      { path: "patients", element: <RoleGuard roles={STAFF_ROLES}><LazyPage><PatientsPage /></LazyPage></RoleGuard> },
      { path: "patient-management", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><PatientManagementWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "organization-workspace", element: <RoleGuard roles={ROUTE_ROLE_POLICIES["/organization-workspace"]}><LazyPage><OrganizationWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "lab-operations", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><LabOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "orders", element: <RoleGuard roles={STAFF_ROLES}><LazyPage><OrdersPage /></LazyPage></RoleGuard> },
      { path: "reports", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><ReportsPage /></LazyPage></RoleGuard> },
      { path: "results", element: <RoleGuard roles={STAFF_ROLES}><LazyPage><ResultsPage /></LazyPage></RoleGuard> },
      { path: "samples", element: <RoleGuard roles={LAB_ROLES}><LazyPage><SamplesPage /></LazyPage></RoleGuard> },
      { path: "labs", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><LabsPage /></LazyPage></RoleGuard> },
      { path: "alerts", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CriticalAlertsPage /></LazyPage></RoleGuard> },
      { path: "notifications", element: <LazyPage><NotificationsPage /></LazyPage> },
      { path: "ai", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><AIPage /></LazyPage></RoleGuard> },
      { path: "ai-platform", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><AiPlatformPage /></LazyPage></RoleGuard> },
      { path: "stats", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><StatsPage /></LazyPage></RoleGuard> },
      { path: "qc", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><QCPage /></LazyPage></RoleGuard> },
      { path: "patient-card", element: <RoleGuard roles={STAFF_ROLES}><LazyPage><PatientCardPage /></LazyPage></RoleGuard> },
      { path: "patient-visit/readiness", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><PatientVisitReadinessPage /></LazyPage></RoleGuard> },
      { path: "identity", element: <RoleGuard roles={STAFF_ROLES}><LazyPage><IdentityPage /></LazyPage></RoleGuard> },
      { path: "tiers", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><TiersPage /></LazyPage></RoleGuard> },
      { path: "compliance", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><CompliancePage /></LazyPage></RoleGuard> },
      { path: "settings", element: <LazyPage><SettingsPage /></LazyPage> },
      { path: "settings/accessibility", element: <LazyPage><AccessibilityCenterPage /></LazyPage> },
      { path: "profile", element: <LazyPage><ProfilePage /></LazyPage> },
      { path: "security", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><SecurityPage /></LazyPage></RoleGuard> },
      { path: "admin/labs", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><AdminLabsPage /></LazyPage></RoleGuard> },
      { path: "admin/users", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><AdminUsersPage /></LazyPage></RoleGuard> },
      { path: "admin/audit", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><AdminAuditPage /></LazyPage></RoleGuard> },
      { path: "fhir", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><FhirPage /></LazyPage></RoleGuard> },
      { path: "ehr", element: <RoleGuard roles={ADMIN_ROLES}><LegacyRouteBridge /></RoleGuard> },
      { path: "hospital", element: <RoleGuard roles={HOSPITAL_OPERATIONS_ROLES}><LazyPage><HospitalOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "edge", element: <RoleGuard roles={ROUTE_ROLE_POLICIES["/edge"]}><LazyPage><EdgePage /></LazyPage></RoleGuard> },
      { path: "financial", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><FinancialPage /></LazyPage></RoleGuard> },
      { path: "financial-governance", element: <RoleGuard roles={FINANCIAL_ROLES}><LazyPage><FinancialGovernancePage /></LazyPage></RoleGuard> },
      { path: "national-data", element: <RoleGuard roles={ROUTE_ROLE_POLICIES["/national-data"]}><LazyPage><NationalDataPage /></LazyPage></RoleGuard> },
      { path: "niam/governance", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NiamGovernancePage /></LazyPage></RoleGuard> },
      { path: "niam/trust", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NiamTrustPage /></LazyPage></RoleGuard> },
      { path: "niam/lifecycle", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NiamLifecyclePage /></LazyPage></RoleGuard> },
      { path: "niam/federation", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NiamFederationPage /></LazyPage></RoleGuard> },
      { path: "niam/certificates", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NiamCertificatesPage /></LazyPage></RoleGuard> },
      { path: "niam/workflows", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NiamWorkflowsPage /></LazyPage></RoleGuard> },
      { path: "niam/adaptive-auth", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NiamAdaptiveAuthPage /></LazyPage></RoleGuard> },
      { path: "ai-fabric", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><AiFabricPageLazy /></LazyPage></RoleGuard> },
      { path: "biomedical", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><BiomedicalApiPageLazy /></LazyPage></RoleGuard> },
      { path: "blood-bank", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><BloodBankApiPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/clinical-foundation", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesClinicalFoundationPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/document-management", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesDocumentManagementPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/encounter-management", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesEncounterManagementPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/healthcare-consent", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesHealthcareConsentPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/provider-management", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesProviderManagementPageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/reporting-service", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesReportingServicePageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/search-service", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesSearchServicePageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/storage-service", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesStorageServicePageLazy /></LazyPage></RoleGuard> },
      { path: "capabilities/workflow-engine", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><CapabilitiesWorkflowEnginePageLazy /></LazyPage></RoleGuard> },
      { path: "certification", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><CertificationPageLazy /></LazyPage></RoleGuard> },
      { path: "citizen", element: <RoleGuard roles={ROUTE_ROLE_POLICIES["/citizen"]}><LazyPage><CitizenWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "my-record", element: <LazyPage><MyRecordPageLazy /></LazyPage> },
      { path: "citizen-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><CitizenPlatformPageLazy /></LazyPage></RoleGuard> },
      { path: "command-center", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><CommandCenterApiPageLazy /></LazyPage></RoleGuard> },
      { path: "command-intelligence", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><CommandIntelligencePageLazy /></LazyPage></RoleGuard> },
      { path: "control-plane", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><ControlPlanePageLazy /></LazyPage></RoleGuard> },
      { path: "acute-care-operations", element: <RoleGuard roles={ACUTE_CARE_OPERATIONS_ROLES}><LazyPage><AcuteCareOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "screen-by-screen", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><ScreenByScreenPageLazy /></LazyPage></RoleGuard> },
      { path: "critical-care", element: <RoleGuard roles={ACUTE_CARE_OPERATIONS_ROLES}><LazyPage><AcuteCareOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "ems", element: <RoleGuard roles={ACUTE_CARE_OPERATIONS_ROLES}><LazyPage><AcuteCareOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "health-data", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><HealthDataPageLazy /></LazyPage></RoleGuard> },
      { path: "integration", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><IntegrationPageLazy /></LazyPage></RoleGuard> },
      { path: "integration/connectors", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><IntegrationConnectorsPageLazy /></LazyPage></RoleGuard> },
      { path: "health-ecosystem", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><HealthEcosystemPageLazy /></LazyPage></RoleGuard> },
      { path: "kernel", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><KernelPageLazy /></LazyPage></RoleGuard> },
      { path: "lifecycle-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><LifecyclePlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/background-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalBackgroundPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/document-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalDocumentPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/ecosystem", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalEcosystemPageLazy /></LazyPage></RoleGuard> },
      { path: "national/ecosystem/gateway", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalEcosystemGatewayPageLazy /></LazyPage></RoleGuard> },
      { path: "national/notification-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalNotificationPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/observability", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalObservabilityApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/rules-engine", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalRulesEngineApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/scheduling-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalSchedulingPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/search-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalSearchPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/task-engine", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalTaskEngineApiPageLazy /></LazyPage></RoleGuard> },
      { path: "national/workflow-runtime", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><NationalWorkflowRuntimeApiPageLazy /></LazyPage></RoleGuard> },
      { path: "pharmacy", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><PharmacyPageLazy /></LazyPage></RoleGuard> },
      { path: "pharmacy-operations", element: <RoleGuard roles={PHARMACY_OPERATIONS_ROLES}><LazyPage><PharmacyOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "radiology-operations", element: <RoleGuard roles={RADIOLOGY_OPERATIONS_ROLES}><LazyPage><RadiologyOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "clinic-operations", element: <RoleGuard roles={CLINIC_OPERATIONS_ROLES}><LazyPage><ClinicOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "hospital-operations", element: <RoleGuard roles={HOSPITAL_OPERATIONS_ROLES}><LazyPage><HospitalOperationsWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "billing-insurance", element: <RoleGuard roles={READONLY_ROLES}><LazyPage><BillingInsuranceWorkspacePageLazy /></LazyPage></RoleGuard> },
      { path: "device-integration", element: <InstitutionalOnlyRoute><RoleGuard roles={READONLY_ROLES}><LazyPage><DeviceIntegrationWorkspacePageLazy /></LazyPage></RoleGuard></InstitutionalOnlyRoute> },
      { path: "pilot-platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><PilotPlatformApiPageLazy /></LazyPage></RoleGuard> },
      { path: "platform", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><PlatformPageLazy /></LazyPage></RoleGuard> },
      { path: "public-health", element: <RoleGuard roles={ADMIN_ROLES}><LazyPage><PublicHealthApiPageLazy /></LazyPage></RoleGuard> },
      { path: "admin", element: <Navigate to="/admin/labs" replace /> },
      { path: "*", element: <LegacyRouteBridge /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
