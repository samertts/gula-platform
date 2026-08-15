import type { UserRole, Permission } from '@/types';

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  master_admin: [
    'patients:read', 'patients:write', 'patients:delete',
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'staff:manage', 'lab:read', 'lab:manage',
    'dashboard:read', 'audit:read',
    'platform:manage_users', 'platform:manage_labs', 'platform:view_stats',
    'system:admin', 'payments:control:read', 'payments:control:request',
    'payments:control:approve', 'payments:control:apply', 'payments:control:emergency',
  ],
  ministry_admin: [
    'patients:read', 'orders:read', 'results:read',
    'lab:read', 'dashboard:read', 'audit:read',
    'platform:manage_users', 'platform:manage_labs', 'platform:view_stats',
  ],
  province_admin: [
    'patients:read', 'orders:read', 'results:read',
    'lab:read', 'dashboard:read', 'audit:read',
    'platform:manage_users', 'platform:manage_labs', 'platform:view_stats',
  ],
  admin: [
    'patients:read', 'patients:write', 'patients:delete',
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'staff:manage', 'lab:read', 'lab:manage',
    'dashboard:read', 'audit:read',
    'platform:manage_users', 'payments:control:read', 'payments:control:request',
  ],
  lab_admin: [
    'patients:read', 'patients:write', 'patients:delete',
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'staff:manage', 'lab:read', 'lab:manage',
    'dashboard:read', 'audit:read',
        'platform:manage_users', 'payments:control:read', 'payments:control:request',
    'popular_clinics:read', 'popular_clinics:manage', 'popular_clinics:patient:read', 'popular_clinics:clinical:write',
    'popular_clinics:prescription:write', 'popular_clinics:dispense:approve', 'popular_clinics:dispense:record', 'popular_clinics:ticket:read',
    'popular_clinics:ticket:issue', 'popular_clinics:ticket:cancel', 'popular_clinics:payment:capture', 'popular_clinics:payment:confirm',
    'popular_clinics:report:daily', 'popular_clinics:report:monthly', 'popular_clinics:workforce:manage',
  ],
  finance_controller: ['dashboard:read', 'audit:read', 'payments:control:read', 'payments:control:approve', 'payments:control:apply', 'popular_clinics:read', 'popular_clinics:payment:confirm', 'popular_clinics:report:daily', 'popular_clinics:report:monthly'],
  refund_reviewer: ['dashboard:read', 'audit:read', 'payments:control:read', 'payments:control:approve'],
  reconciler: ['dashboard:read', 'audit:read', 'payments:control:read', 'payments:control:apply', 'popular_clinics:read', 'popular_clinics:report:daily', 'popular_clinics:report:monthly'],
  finance_auditor: ['dashboard:read', 'audit:read', 'payments:control:read', 'popular_clinics:read', 'popular_clinics:report:daily', 'popular_clinics:report:monthly'],
  finance_operator: ['dashboard:read', 'payments:control:read', 'payments:control:request', 'popular_clinics:read', 'popular_clinics:patient:read', 'popular_clinics:ticket:read', 'popular_clinics:report:daily'],
  cashier: ['dashboard:read', 'payments:control:read', 'payments:control:request', 'popular_clinics:read', 'popular_clinics:patient:read', 'popular_clinics:ticket:read', 'popular_clinics:ticket:issue', 'popular_clinics:ticket:cancel', 'popular_clinics:payment:capture', 'popular_clinics:report:daily'],
  doctor: [
    'patients:read', 'orders:read', 'results:read',
    'lab:read', 'dashboard:read',
    'popular_clinics:read', 'popular_clinics:patient:read', 'popular_clinics:clinical:write', 'popular_clinics:prescription:write', 'popular_clinics:ticket:read', 'popular_clinics:report:monthly',
  ],
  staff: [
    'patients:read', 'patients:write',
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'lab:read', 'dashboard:read',
  ],
  lab_staff: [
    'patients:read', 'patients:write',
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'lab:read', 'dashboard:read',
  ],
  technician: [
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'lab:read', 'dashboard:read',
    'popular_clinics:read', 'popular_clinics:patient:read', 'popular_clinics:clinical:write', 'popular_clinics:dispense:record',
  ],
  receptionist: ['patients:read', 'popular_clinics:read', 'popular_clinics:patient:read', 'popular_clinics:ticket:read', 'popular_clinics:ticket:issue'],
  citizen: [],
  // Synthetic demo identity: read-only shell access only; no clinical or admin permissions.
  demo_viewer: ['dashboard:read'],
};

export function hasPermission(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

export function hasAnyPermission(role: UserRole, permissions: Permission[]): boolean {
  return permissions.some((p) => hasPermission(role, p));
}

export function hasAllPermissions(role: UserRole, permissions: Permission[]): boolean {
  return permissions.every((p) => hasPermission(role, p));
}

export function canManageRole(actorRole: UserRole, targetRole: UserRole): boolean {
  const levels: Record<UserRole, number> = {
    master_admin: 100, ministry_admin: 90, province_admin: 80,
    admin: 50, lab_admin: 50, finance_controller: 70, refund_reviewer: 60,
    reconciler: 55, finance_auditor: 45, finance_operator: 35, cashier: 25,
    doctor: 40, staff: 20, lab_staff: 20, technician: 20, receptionist: 25, citizen: 10, demo_viewer: 0,
  };
  return (levels[actorRole] ?? 0) > (levels[targetRole] ?? 0);
}

export function getVisiblePermissions(role: UserRole): Permission[] {
  return ROLE_PERMISSIONS[role] ?? [];
}
