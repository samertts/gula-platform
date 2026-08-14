import { useAuth } from "@/contexts/AuthContext";
import { hasPermission } from "@/permissions";
import { hasReflectedPermission } from "@/permissions/liveCapabilities";

export function usePermissions() {
  const { user, demoMode, effectivePermissions } = useAuth();
  const role = user?.role ?? "citizen";
  const can = (permission: string) => {
    if (demoMode) return hasPermission(role, permission);
    // Live capabilities are UX hints only; protected APIs enforce on the server.
    return hasReflectedPermission(effectivePermissions, [permission]);
  };

  return {
    can,
    role,
    isAdmin: can("system:admin"),
    isPlatformAdmin: can("platform:manage_labs"),
    canManageUsers: can("platform:manage_users"),
    canReadPatients: can("patients:read"),
    canWritePatients: can("patients:write"),
    canReadOrders: can("orders:read"),
    canWriteOrders: can("orders:write"),
    canReadResults: can("results:read"),
    canWriteResults: can("results:write"),
    canManageStaff: can("staff:manage"),
    canReadAudit: can("audit:read"),
  };
}
