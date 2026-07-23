export const ROLE_LEVELS: Record<string, number> = {
  master_admin: 100,
  ministry_admin: 90,
  province_admin: 80,
  admin: 50,
  lab_admin: 50,
  doctor: 40,
  technician: 20,
  staff: 20,
  receptionist: 25,
  citizen: 10,
};

export const ROLE_PERMISSIONS: Record<string, string[]> = {
  master_admin: [
    "patients:read", "patients:write", "patients:delete",
    "orders:read", "orders:write",
    "results:read", "results:write",
    "staff:manage", "lab:read", "lab:manage",
    "dashboard:read", "audit:read",
    "platform:manage_labs", "platform:manage_users", "platform:view_stats",
    "system:admin",
  ],
  ministry_admin: [
    "patients:read", "orders:read", "results:read", "lab:read",
    "dashboard:read", "audit:read",
    "platform:manage_labs", "platform:manage_users", "platform:view_stats",
  ],
  province_admin: [
    "patients:read", "orders:read", "results:read", "lab:read",
    "dashboard:read", "audit:read",
    "platform:manage_labs", "platform:manage_users", "platform:view_stats",
  ],
  admin: [
    "patients:read", "patients:write", "patients:delete",
    "orders:read", "orders:write",
    "results:read", "results:write",
    "staff:manage", "lab:read", "lab:manage",
    "dashboard:read", "audit:read",
    "platform:manage_users",
  ],
  doctor: [
    "patients:read", "orders:read", "results:read", "dashboard:read",
  ],
  technician: [
    "orders:read", "orders:write",
    "results:read", "results:write",
    "lab:read", "dashboard:read",
  ],
  staff: [
    "patients:read", "patients:write",
    "orders:read", "orders:write",
    "results:read", "results:write",
    "lab:read", "dashboard:read",
  ],
  citizen: [],
};

export function hasPermission(role: string, permission: string): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

export function hasAnyPermission(role: string, permissions: string[]): boolean {
  return permissions.some((p) => hasPermission(role, p));
}

export function canManageRole(actorRole: string, targetRole: string): boolean {
  if (targetRole === "master_admin") return actorRole === "master_admin";
  const actorLevel = ROLE_LEVELS[actorRole] ?? 0;
  const targetLevel = ROLE_LEVELS[targetRole] ?? 0;
  return actorLevel > targetLevel && actorLevel > 0;
}

export function getRoleLevel(role: string): number {
  return ROLE_LEVELS[role] ?? 0;
}

export function isPlatformRole(role: string): boolean {
  return ["master_admin", "ministry_admin", "province_admin"].includes(role);
}

export const NAV_ITEMS: Record<string, { label: string; path: string; icon: string; permissions?: string[] }[]> = {
  main: [
    { label: "nav.dashboard", path: "/dashboard", icon: "LayoutDashboard", permissions: ["dashboard:read"] },
    { label: "nav.patients", path: "/patients", icon: "Users", permissions: ["patients:read"] },
    { label: "nav.orders", path: "/orders", icon: "ClipboardList", permissions: ["orders:read"] },
    { label: "nav.results", path: "/results", icon: "FlaskConical", permissions: ["results:read"] },
    { label: "nav.samples", path: "/samples", icon: "TestTube", permissions: ["orders:read"] },
  ],
  lab: [
    { label: "nav.qc", path: "/qc", icon: "ShieldCheck", permissions: ["results:read"] },
    { label: "nav.alerts", path: "/alerts", icon: "BellRing", permissions: ["results:read"] },
  ],
  admin: [
    { label: "nav.admin", path: "/admin", icon: "Shield", permissions: ["platform:manage_users"] },
    { label: "nav.labs", path: "/labs", icon: "Building2", permissions: ["lab:read"] },
    { label: "nav.stats", path: "/stats", icon: "BarChart3", permissions: ["dashboard:read"] },
    { label: "nav.compliance", path: "/compliance", icon: "FileCheck", permissions: ["audit:read"] },
  ],
  tools: [
    { label: "nav.ai", path: "/ai", icon: "Brain", permissions: ["dashboard:read"] },
    { label: "nav.aiPlatform", path: "/ai-platform", icon: "Brain", permissions: ["dashboard:read"] },
    { label: "nav.patientCard", path: "/patient-card", icon: "CreditCard", permissions: ["patients:read"] },
    { label: "nav.identity", path: "/identity", icon: "Fingerprint", permissions: ["patients:read"] },
    { label: "nav.tiers", path: "/tiers", icon: "Crown", permissions: ["dashboard:read"] },
  ],
  enterprise: [
    { label: "nav.hospital", path: "/hospital", icon: "Building", permissions: ["lab:read"] },
    { label: "nav.edgePlatform", path: "/edge", icon: "Server", permissions: ["system:admin"] },
    { label: "nav.financial", path: "/financial", icon: "DollarSign", permissions: ["lab:manage"] },
    { label: "nav.nationalData", path: "/national-data", icon: "BarChart3", permissions: ["patients:read"] },
  ],
  niam: [
    { label: "حوكمة الهوية", path: "/niam/governance", icon: "Scale", permissions: ["system:admin"] },
    { label: "إطار الثقة", path: "/niam/trust", icon: "Shield", permissions: ["system:admin"] },
    { label: "دورة الحياة", path: "/niam/lifecycle", icon: "UserCircle", permissions: ["system:admin"] },
    { label: "الاتحاد", path: "/niam/federation", icon: "Globe", permissions: ["system:admin"] },
    { label: "الشهادات", path: "/niam/certificates", icon: "Certificate", permissions: ["system:admin"] },
    { label: "سير العمل", path: "/niam/workflows", icon: "Workflow", permissions: ["system:admin"] },
    { label: "المصادقة التكيفية", path: "/niam/adaptive-auth", icon: "ShieldCheck", permissions: ["system:admin"] },
  ],
  settings: [
    { label: "nav.profile", path: "/profile", icon: "UserCircle" },
    { label: "nav.settings", path: "/settings", icon: "Settings" },
    { label: "nav.security", path: "/security", icon: "Lock" },
    { label: "nav.notifications", path: "/notifications", icon: "Bell" },
  ],
};
