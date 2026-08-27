type RouteLoader = () => Promise<unknown>;

const routeLoaders: Record<string, RouteLoader> = {
  "/dashboard": () => import("@/pages/dashboard/DashboardPage"),
  "/my-record": () => import("@/pages/my-record/MyRecordPage"),
  "/patients": () => import("@/pages/patients/PatientsPage"),
  "/orders": () => import("@/pages/orders/OrdersPage"),
  "/results": () => import("@/pages/results/ResultsPage"),
  "/notifications": () => import("@/pages/notifications/NotificationsPage"),
  "/patient-management": () => import("@/pages/patients/PatientManagementWorkspacePage"),
  "/lab-operations": () => import("@/pages/lab/LabOperationsWorkspacePage"),
  "/radiology-operations": () => import("@/pages/radiology/RadiologyOperationsWorkspacePage"),
  "/pharmacy-operations": () => import("@/pages/pharmacy/PharmacyOperationsWorkspacePage"),
};

const prefetchedRoutes = new Set<string>();

/**
 * Warm only the code chunk for a visible, already-authorized navigation item.
 * This intentionally does not call APIs, resolve workspaces, or alter server authority.
 */
export function prefetchRoute(path: string): void {
  const loader = routeLoaders[path];
  if (!loader || prefetchedRoutes.has(path)) return;

  prefetchedRoutes.add(path);
  void loader().catch(() => {
    // Navigation remains the source of truth; a failed prefetch is retried by lazy().
    prefetchedRoutes.delete(path);
  });
}
