import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/auth.store";

/* Pages */
import LoginPage     from "./pages/auth/LoginPage";
import RegisterPage  from "./pages/auth/RegisterPage";
import Layout        from "./components/Layout";

/* Lab Pages */
import LabDashboard    from "./pages/lab/LabDashboard";
import SamplesPage     from "./pages/lab/SamplesPage";
import ResultsEntry    from "./pages/lab/ResultsEntry";
import OrdersPage      from "./pages/lab/OrdersPage";
import WorkQueuePage   from "./pages/lab/WorkQueuePage";
import ApprovalPage    from "./pages/lab/ApprovalPage";
import CriticalValuesPage from "./pages/lab/CriticalValuesPage";

/* Doctor Pages */
import DoctorDashboard from "./pages/doctor/DoctorDashboard";
import PatientsPage    from "./pages/doctor/PatientsPage";
import PatientDetail   from "./pages/doctor/PatientDetail";
import NewOrderPage    from "./pages/doctor/NewOrderPage";

/* Patient Pages */
import PatientDashboard from "./pages/patient/PatientDashboard";
import MyResultsPage    from "./pages/patient/MyResultsPage";
import MyOrdersPage     from "./pages/patient/MyOrdersPage";
import TrackOrderPage   from "./pages/patient/TrackOrderPage";
import ReportPage       from "./pages/patient/ReportPage";

/* Admin Pages */
import AdminDashboard  from "./pages/admin/AdminDashboard";
import CatalogPage     from "./pages/admin/CatalogPage";
import UsersPage       from "./pages/admin/UsersPage";
import LinkPatientPage from "./pages/admin/LinkPatientPage";

/* Shared Pages */
import ProfilePage     from "./pages/shared/ProfilePage";

/* ---------------------------------------------------------------- */

function PrivateRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function DashboardRedirect() {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" />;
  if (user.role === "admin")     return <Navigate to="/admin" />;
  if (user.role === "lab_staff") return <Navigate to="/lab" />;
  if (user.role === "doctor")    return <Navigate to="/doctor" />;
  return <Navigate to="/portal" />;
}

/* ---------------------------------------------------------------- */

export default function App() {
  const { user } = useAuthStore();

  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login"    element={user ? <DashboardRedirect /> : <LoginPage />} />
        <Route path="/register" element={user ? <DashboardRedirect /> : <RegisterPage />} />
        <Route path="/"         element={<DashboardRedirect />} />
        <Route path="/dashboard" element={<DashboardRedirect />} />

        {/* Lab Staff */}
        <Route path="/lab" element={
          <PrivateRoute roles={["lab_staff", "admin"]}>
            <Layout role="lab" />
          </PrivateRoute>
        }>
          <Route index              element={<LabDashboard />} />
          <Route path="orders"      element={<OrdersPage />} />
          <Route path="samples"     element={<SamplesPage />} />
          <Route path="results"     element={<ResultsEntry />} />
          <Route path="queue"       element={<WorkQueuePage />} />
          <Route path="approval"    element={<ApprovalPage />} />
          <Route path="critical"    element={<CriticalValuesPage />} />
          <Route path="profile"     element={<ProfilePage />} />
        </Route>

        {/* Doctor */}
        <Route path="/doctor" element={
          <PrivateRoute roles={["doctor", "admin"]}>
            <Layout role="doctor" />
          </PrivateRoute>
        }>
          <Route index                   element={<DoctorDashboard />} />
          <Route path="patients"         element={<PatientsPage />} />
          <Route path="patients/:id"     element={<PatientDetail />} />
          <Route path="orders/new"       element={<NewOrderPage />} />
          <Route path="profile"          element={<ProfilePage />} />
        </Route>

        {/* Patient / Citizen Portal */}
        <Route path="/portal" element={
          <PrivateRoute roles={["patient", "citizen"]}>
            <Layout role="patient" />
          </PrivateRoute>
        }>
          <Route index                    element={<PatientDashboard />} />
          <Route path="results"           element={<MyResultsPage />} />
          <Route path="orders"            element={<MyOrdersPage />} />
          <Route path="orders/:id/track"  element={<TrackOrderPage />} />
          <Route path="reports/:id"       element={<ReportPage />} />
          <Route path="profile"           element={<ProfilePage />} />
        </Route>

        {/* Admin */}
        <Route path="/admin" element={
          <PrivateRoute roles={["admin"]}>
            <Layout role="admin" />
          </PrivateRoute>
        }>
          <Route index                element={<AdminDashboard />} />
          <Route path="catalog"       element={<CatalogPage />} />
          <Route path="users"         element={<UsersPage />} />
          <Route path="link-patient"  element={<LinkPatientPage />} />
          <Route path="profile"       element={<ProfilePage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
