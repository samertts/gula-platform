import type { UserRole, Permission } from '@/types';

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  master_admin: [
    'patients:read', 'patients:write', 'patients:delete',
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'staff:manage', 'lab:read', 'lab:manage',
    'dashboard:read', 'audit:read',
    'platform:manage_users', 'platform:manage_labs', 'platform:view_stats',
    'system:admin',
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
    'platform:manage_users',
  ],
  lab_admin: [
    'patients:read', 'patients:write', 'patients:delete',
    'orders:read', 'orders:write',
    'results:read', 'results:write',
    'staff:manage', 'lab:read', 'lab:manage',
    'dashboard:read', 'audit:read',
    'platform:manage_users',
  ],
  doctor: [
    'patients:read', 'orders:read', 'results:read',
    'lab:read', 'dashboard:read',
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
  ],
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
    admin: 50, lab_admin: 50, doctor: 40, staff: 20,
    lab_staff: 20, technician: 20, citizen: 10, demo_viewer: 0,
  };
  return (levels[actorRole] ?? 0) > (levels[targetRole] ?? 0);
}

export function getVisiblePermissions(role: UserRole): Permission[] {
  return ROLE_PERMISSIONS[role] ?? [];
}
