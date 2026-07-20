import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { useAuth } from '@/contexts/AuthContext';
import { Skeleton } from '@/components/ui/Skeleton';

const LoginPage = lazy(() => import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const PatientsPage = lazy(() => import('@/pages/PatientsPage').then((m) => ({ default: m.PatientsPage })));
const PatientDetailPage = lazy(() => import('@/pages/PatientDetailPage').then((m) => ({ default: m.PatientDetailPage })));
const OrdersPage = lazy(() => import('@/pages/OrdersPage').then((m) => ({ default: m.OrdersPage })));
const OrderDetailPage = lazy(() => import('@/pages/OrderDetailPage').then((m) => ({ default: m.OrderDetailPage })));
const ResultsPage = lazy(() => import('@/pages/ResultsPage').then((m) => ({ default: m.ResultsPage })));
const SamplesPage = lazy(() => import('@/pages/SamplesPage').then((m) => ({ default: m.SamplesPage })));
const QualityControlPage = lazy(() => import('@/pages/QualityControlPage').then((m) => ({ default: m.QualityControlPage })));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then((m) => ({ default: m.AnalyticsPage })));
const CriticalAlertsPage = lazy(() => import('@/pages/CriticalAlertsPage').then((m) => ({ default: m.CriticalAlertsPage })));
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));
const MFAPage = lazy(() => import('@/pages/MFAPage').then((m) => ({ default: m.MFAPage })));
const SecurityLogsPage = lazy(() => import('@/pages/SecurityLogsPage').then((m) => ({ default: m.SecurityLogsPage })));
const AdminUsersPage = lazy(() => import('@/pages/AdminUsersPage').then((m) => ({ default: m.AdminUsersPage })));
const AdminLabsPage = lazy(() => import('@/pages/AdminLabsPage').then((m) => ({ default: m.AdminLabsPage })));
const AdminAuditLogPage = lazy(() => import('@/pages/AdminAuditLogPage').then((m) => ({ default: m.AdminAuditLogPage })));

function LazyFallback() {
  return (
    <div className="p-6 space-y-4">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-64" />
      <div className="grid grid-cols-3 gap-4 mt-6">
        {[1,2,3].map((i) => <Skeleton key={i} className="h-32" />)}
      </div>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LazyFallback />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LazyFallback />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function LazyPage({ element }: { element: React.ReactNode }) {
  return <Suspense fallback={<LazyFallback />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <PublicRoute><AuthLayout /></PublicRoute>,
    children: [{ index: true, element: <LazyPage element={<LoginPage />} /> }],
  },
  {
    path: '/',
    element: <ProtectedRoute><DashboardLayout /></ProtectedRoute>,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <LazyPage element={<DashboardPage />} /> },
      { path: 'patients', element: <LazyPage element={<PatientsPage />} /> },
      { path: 'patients/:id', element: <LazyPage element={<PatientDetailPage />} /> },
      { path: 'orders', element: <LazyPage element={<OrdersPage />} /> },
      { path: 'orders/:id', element: <LazyPage element={<OrderDetailPage />} /> },
      { path: 'results', element: <LazyPage element={<ResultsPage />} /> },
      { path: 'samples', element: <LazyPage element={<SamplesPage />} /> },
      { path: 'quality-control', element: <LazyPage element={<QualityControlPage />} /> },
      { path: 'analytics', element: <LazyPage element={<AnalyticsPage />} /> },
      { path: 'alerts', element: <LazyPage element={<CriticalAlertsPage />} /> },
      { path: 'settings', element: <LazyPage element={<SettingsPage />} /> },
      { path: 'security/mfa', element: <LazyPage element={<MFAPage />} /> },
      { path: 'security/logs', element: <LazyPage element={<SecurityLogsPage />} /> },
      {
        path: 'admin',
        children: [
          { index: true, element: <Navigate to="/admin/users" replace /> },
          { path: 'users', element: <LazyPage element={<AdminUsersPage />} /> },
          { path: 'labs', element: <LazyPage element={<AdminLabsPage />} /> },
          { path: 'audit-log', element: <LazyPage element={<AdminAuditLogPage />} /> },
        ],
      },
    ],
  },
]);
