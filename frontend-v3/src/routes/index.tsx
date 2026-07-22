import { createBrowserRouter, Navigate } from "react-router-dom";
import { lazy, Suspense, type ReactNode } from "react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { LoadingSpinner } from "@/components/shared/PageComponents";

const LoginPage = lazy(() => import("@/pages/auth/LoginPage").then(m => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import("@/pages/dashboard/DashboardPage").then(m => ({ default: m.DashboardPage })));
const PatientsPage = lazy(() => import("@/pages/patients/PatientsPage").then(m => ({ default: m.PatientsPage })));
const OrdersPage = lazy(() => import("@/pages/orders/OrdersPage").then(m => ({ default: m.OrdersPage })));
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
const EhrPage = lazy(() => import("@/pages/ehr/EhrPage").then(m => ({ default: m.EhrPage })));
const HospitalPage = lazy(() => import("@/pages/hospital/HospitalPage").then(m => ({ default: m.HospitalPage })));
const EdgePage = lazy(() => import("@/pages/edge/EdgePage").then(m => ({ default: m.EdgePage })));
const FinancialPage = lazy(() => import("@/pages/financial/FinancialPage").then(m => ({ default: m.FinancialPage })));
const NationalDataPage = lazy(() => import("@/pages/national-data/NationalDataPage").then(m => ({ default: m.NationalDataPage })));

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = localStorage.getItem("access_token");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function LazyPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<LoadingSpinner />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AuthLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: "login", element: <LazyPage><LoginPage /></LazyPage> },
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
      { path: "patients", element: <LazyPage><PatientsPage /></LazyPage> },
      { path: "orders", element: <LazyPage><OrdersPage /></LazyPage> },
      { path: "results", element: <LazyPage><ResultsPage /></LazyPage> },
      { path: "samples", element: <LazyPage><SamplesPage /></LazyPage> },
      { path: "labs", element: <LazyPage><LabsPage /></LazyPage> },
      { path: "alerts", element: <LazyPage><CriticalAlertsPage /></LazyPage> },
      { path: "notifications", element: <LazyPage><NotificationsPage /></LazyPage> },
      { path: "ai", element: <LazyPage><AIPage /></LazyPage> },
      { path: "ai-platform", element: <LazyPage><AiPlatformPage /></LazyPage> },
      { path: "stats", element: <LazyPage><StatsPage /></LazyPage> },
      { path: "qc", element: <LazyPage><QCPage /></LazyPage> },
      { path: "patient-card", element: <LazyPage><PatientCardPage /></LazyPage> },
      { path: "identity", element: <LazyPage><IdentityPage /></LazyPage> },
      { path: "tiers", element: <LazyPage><TiersPage /></LazyPage> },
      { path: "compliance", element: <LazyPage><CompliancePage /></LazyPage> },
      { path: "settings", element: <LazyPage><SettingsPage /></LazyPage> },
      { path: "profile", element: <LazyPage><ProfilePage /></LazyPage> },
      { path: "security", element: <LazyPage><SecurityPage /></LazyPage> },
      { path: "admin/labs", element: <LazyPage><AdminLabsPage /></LazyPage> },
      { path: "admin/users", element: <LazyPage><AdminUsersPage /></LazyPage> },
      { path: "admin/audit", element: <LazyPage><AdminAuditPage /></LazyPage> },
      { path: "fhir", element: <LazyPage><FhirPage /></LazyPage> },
      { path: "ehr", element: <LazyPage><EhrPage /></LazyPage> },
      { path: "hospital", element: <LazyPage><HospitalPage /></LazyPage> },
      { path: "edge", element: <LazyPage><EdgePage /></LazyPage> },
      { path: "financial", element: <LazyPage><FinancialPage /></LazyPage> },
      { path: "national-data", element: <LazyPage><NationalDataPage /></LazyPage> },
      { path: "admin", element: <Navigate to="/admin/labs" replace /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
