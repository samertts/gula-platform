import { useAuth } from "@/contexts/AuthContext";
import { hasPermission } from "@/permissions";

export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role ?? "citizen";

  return {
    can: (permission: string) => hasPermission(role, permission),
    role,
    isAdmin: hasPermission(role, "system:admin"),
    isPlatformAdmin: hasPermission(role, "platform:manage_labs"),
    canManageUsers: hasPermission(role, "platform:manage_users"),
    canReadPatients: hasPermission(role, "patients:read"),
    canWritePatients: hasPermission(role, "patients:write"),
    canReadOrders: hasPermission(role, "orders:read"),
    canWriteOrders: hasPermission(role, "orders:write"),
    canReadResults: hasPermission(role, "results:read"),
    canWriteResults: hasPermission(role, "results:write"),
    canManageStaff: hasPermission(role, "staff:manage"),
    canReadAudit: hasPermission(role, "audit:read"),
  };
}
