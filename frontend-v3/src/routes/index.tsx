import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "@/layouts/AuthLayout";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { LoginPage } from "@/pages/auth/LoginPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { PatientsPage } from "@/pages/patients/PatientsPage";
import { OrdersPage } from "@/pages/orders/OrdersPage";
import { ResultsPage } from "@/pages/results/ResultsPage";
import { SamplesPage } from "@/pages/samples/SamplesPage";
import { LabsPage } from "@/pages/labs/LabsPage";
import { CriticalAlertsPage } from "@/pages/alerts/CriticalAlertsPage";
import { NotificationsPage } from "@/pages/notifications/NotificationsPage";
import { AIPage } from "@/pages/ai/AIPage";
import { StatsPage } from "@/pages/stats/StatsPage";
import { QCPage } from "@/pages/qc/QCPage";
import { PatientCardPage } from "@/pages/patient-card/PatientCardPage";
import { IdentityPage } from "@/pages/identity/IdentityPage";
import { TiersPage } from "@/pages/tiers/TiersPage";
import { CompliancePage } from "@/pages/compliance/CompliancePage";
import { SettingsPage } from "@/pages/settings/SettingsPage";
import { ProfilePage } from "@/pages/profile/ProfilePage";
import { SecurityPage } from "@/pages/security/SecurityPage";
import { AdminLabsPage, AdminUsersPage, AdminAuditPage } from "@/pages/admin/AdminPages";
import { FhirPage } from "@/pages/fhir/FhirPage";
import { type ReactNode } from "react";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = localStorage.getItem("access_token");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AuthLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: "login", element: <LoginPage /> },
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
      { path: "dashboard", element: <DashboardPage /> },
      { path: "patients", element: <PatientsPage /> },
      { path: "orders", element: <OrdersPage /> },
      { path: "results", element: <ResultsPage /> },
      { path: "samples", element: <SamplesPage /> },
      { path: "labs", element: <LabsPage /> },
      { path: "alerts", element: <CriticalAlertsPage /> },
      { path: "notifications", element: <NotificationsPage /> },
      { path: "ai", element: <AIPage /> },
      { path: "stats", element: <StatsPage /> },
      { path: "qc", element: <QCPage /> },
      { path: "patient-card", element: <PatientCardPage /> },
      { path: "identity", element: <IdentityPage /> },
      { path: "tiers", element: <TiersPage /> },
      { path: "compliance", element: <CompliancePage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "security", element: <SecurityPage /> },
      { path: "admin/labs", element: <AdminLabsPage /> },
      { path: "admin/users", element: <AdminUsersPage /> },
      { path: "admin/audit", element: <AdminAuditPage /> },
      { path: "fhir", element: <FhirPage /> },
      { path: "admin", element: <Navigate to="/admin/labs" replace /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
