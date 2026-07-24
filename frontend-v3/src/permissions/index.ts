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
  clinical: [
    { label: "الأسس السريرية", path: "/capabilities/clinical-foundation", icon: "Heart", permissions: ["dashboard:read"] },
    { label: "إدارة المستندات", path: "/capabilities/document-management", icon: "FileText", permissions: ["dashboard:read"] },
    { label: "إدارة الزيارات", path: "/capabilities/encounter-management", icon: "CalendarDays", permissions: ["dashboard:read"] },
    { label: "الموافقة الصحية", path: "/capabilities/healthcare-consent", icon: "FileCheck", permissions: ["dashboard:read"] },
    { label: "إدارة المزودين", path: "/capabilities/provider-management", icon: "Building2", permissions: ["dashboard:read"] },
    { label: "خدمة التقارير", path: "/capabilities/reporting-service", icon: "BarChart3", permissions: ["dashboard:read"] },
    { label: "خدمة البحث", path: "/capabilities/search-service", icon: "Search", permissions: ["dashboard:read"] },
    { label: "خدمة التخزين", path: "/capabilities/storage-service", icon: "HardDrive", permissions: ["dashboard:read"] },
    { label: "محرك سير العمل", path: "/capabilities/workflow-engine", icon: "Workflow", permissions: ["dashboard:read"] }
  ],
  national: [
    { label: "الخلفية الوطنية", path: "/national/background-platform", icon: "Clock", permissions: ["dashboard:read"] },
    { label: "الوثائق الوطنية", path: "/national/document-platform", icon: "FileText", permissions: ["dashboard:read"] },
    { label: "النظام البيئي", path: "/national/ecosystem", icon: "ShareNetwork", permissions: ["dashboard:read"] },
    { label: "بوابة النظام البيئي", path: "/national/ecosystem/gateway", icon: "Router", permissions: ["dashboard:read"] },
    { label: "الإشعارات الوطنية", path: "/national/notification-platform", icon: "Bell", permissions: ["dashboard:read"] },
    { label: "المراقبة الوطنية", path: "/national/observability", icon: "Eye", permissions: ["dashboard:read"] },
    { label: "محرك القواعد", path: "/national/rules-engine", icon: "Braces", permissions: ["dashboard:read"] },
    { label: "الجدولة الوطنية", path: "/national/scheduling-platform", icon: "Calendar", permissions: ["dashboard:read"] },
    { label: "البحث الوطني", path: "/national/search-platform", icon: "Search", permissions: ["dashboard:read"] },
    { label: "محرك المهام", path: "/national/task-engine", icon: "ListChecks", permissions: ["dashboard:read"] },
    { label: "تشغيل سير العمل", path: "/national/workflow-runtime", icon: "PlayCircle", permissions: ["dashboard:read"] }
  ],
  systems: [
    { label: "منصة الذكاء الاصطناعي", path: "/ai-fabric", icon: "Brain", permissions: ["system:admin"] },
    { label: "الطب الحيوي", path: "/biomedical", icon: "Microscope", permissions: ["system:admin"] },
    { label: "بنك الدم", path: "/blood-bank", icon: "Droplets", permissions: ["system:admin"] },
    { label: "الشهادات", path: "/certification", icon: "ScrollText", permissions: ["system:admin"] },
    { label: "منصة المواطن", path: "/citizen-platform", icon: "UserCheck", permissions: ["system:admin"] },
    { label: "مركز القيادة", path: "/command-center", icon: "Monitor", permissions: ["system:admin"] },
    { label: "الاستخبارات", path: "/command-intelligence", icon: "BrainCircuit", permissions: ["system:admin"] },
    { label: "طائرة التحكم", path: "/control-plane", icon: "Gamepad2", permissions: ["system:admin"] },
    { label: "العناية الحرجة", path: "/critical-care", icon: "HeartPulse", permissions: ["system:admin"] },
    { label: "الطوارئ", path: "/ems", icon: "Ambulance", permissions: ["system:admin"] },
    { label: "البيانات الصحية", path: "/health-data", icon: "Database", permissions: ["system:admin"] },
    { label: "التكامل", path: "/integration", icon: "Cable", permissions: ["system:admin"] },
    { label: "النواة", path: "/kernel", icon: "Cpu", permissions: ["system:admin"] },
    { label: "دورة حياة المنصة", path: "/lifecycle-platform", icon: "RefreshCw", permissions: ["system:admin"] },
    { label: "الصيدلة", path: "/pharmacy", icon: "Pill", permissions: ["system:admin"] },
    { label: "المنصة التجريبية", path: "/pilot-platform", icon: "FlaskConical", permissions: ["system:admin"] },
    { label: "المنصة", path: "/platform", icon: "Layers", permissions: ["system:admin"] },
    { label: "الصحة العامة", path: "/public-health", icon: "Activity", permissions: ["system:admin"] },
    { label: "التوافق الصحي FHIR", path: "/fhir", icon: "Share2", permissions: ["system:admin"] },
  ],
};
