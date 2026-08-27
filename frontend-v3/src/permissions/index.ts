import type { UserRole } from "@/types";
import {
  ADMIN_ROLES,
  FINANCIAL_ROLES,
  LAB_OPERATIONS_ROLES,
  LAB_ROLES,
  READONLY_ROLES,
  ORGANIZATION_ROLES,
  PHARMACY_OPERATIONS_ROLES,
  RADIOLOGY_OPERATIONS_ROLES,
  CLINIC_OPERATIONS_ROLES,
  HOSPITAL_OPERATIONS_ROLES,
  ACUTE_CARE_OPERATIONS_ROLES,
  ROUTE_ROLE_POLICIES,
  STAFF_ROLES,
} from "./routePolicies";

export const ROLE_LEVELS: Record<string, number> = {
  master_admin: 100,
  ministry_admin: 90,
  province_admin: 80,
  admin: 50,
  lab_admin: 50,
  finance_controller: 70,
  refund_reviewer: 60,
  reconciler: 55,
  finance_auditor: 45,
  finance_operator: 35,
  cashier: 25,
  doctor: 40,
  technician: 20,
  staff: 20,
  lab_staff: 20,
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
    "payments:control:read", "payments:control:request",
    "orders:read", "orders:write",
    "results:read", "results:write",
    "staff:manage", "lab:read", "lab:manage",
    "dashboard:read", "audit:read",
    "platform:manage_users",
  ],
  lab_admin: [
    "patients:read", "patients:write",
    "payments:control:read", "payments:control:request",
    "orders:read", "orders:write",
    "results:read", "results:write",
    "staff:manage", "lab:read", "lab:manage",
    "dashboard:read", "audit:read",
  ],
  finance_controller: ["dashboard:read", "audit:read", "payments:control:read", "payments:control:approve", "payments:control:apply"],
  refund_reviewer: ["dashboard:read", "audit:read", "payments:control:read", "payments:control:approve"],
  reconciler: ["dashboard:read", "audit:read", "payments:control:read", "payments:control:apply"],
  finance_auditor: ["dashboard:read", "audit:read", "payments:control:read"],
  finance_operator: ["dashboard:read", "payments:control:read", "payments:control:request"],
  cashier: ["dashboard:read", "payments:control:read", "payments:control:request"],
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
  lab_staff: [
    "orders:read", "orders:write",
    "results:read", "results:write",
    "lab:read", "dashboard:read",
  ],
  citizen: ["citizen:workspace"],
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

export type NavigationItem = {
  label: string;
  path: string;
  icon: string;
  permissions?: string[];
  roles?: readonly UserRole[];
  institutionalOnly?: boolean;
};

export const NAV_ITEMS: Record<string, NavigationItem[]> = {
  main: [
    { label: "nav.dashboard", path: "/dashboard", icon: "LayoutDashboard", permissions: ["dashboard:read"] },
    { label: "مركز هويتي ومساحاتي", path: "/my-record", icon: "UserCircle" },
    { label: "بوابة المؤسسة الصحية", path: "/organization-workspace", icon: "Building2", permissions: ["dashboard:read"], roles: ORGANIZATION_ROLES },
    { label: "nav.citizenWorkspace", path: "/citizen", icon: "UserCircle", permissions: ["citizen:workspace"], roles: ROUTE_ROLE_POLICIES["/citizen"] },
    { label: "nav.patients", path: "/patients", icon: "Users", permissions: ["patients:read"], roles: STAFF_ROLES },
    { label: "إدارة المرضى المتقدمة", path: "/patient-management", icon: "HeartPulse", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "إدارة المختبر", path: "/lab-operations", icon: "FlaskConical", permissions: ["dashboard:read"], roles: LAB_OPERATIONS_ROLES },
    { label: "nav.orders", path: "/orders", icon: "ClipboardList", permissions: ["orders:read"], roles: STAFF_ROLES },
    { label: "nav.reports", path: "/reports", icon: "FileBarChart2", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "nav.results", path: "/results", icon: "FlaskConical", permissions: ["results:read"], roles: STAFF_ROLES },
    { label: "nav.samples", path: "/samples", icon: "TestTube", permissions: ["orders:read"], roles: LAB_ROLES },
  ],
  lab: [
    { label: "nav.qc", path: "/qc", icon: "ShieldCheck", permissions: ["results:read"], roles: READONLY_ROLES },
    { label: "nav.alerts", path: "/alerts", icon: "BellRing", permissions: ["results:read"], roles: READONLY_ROLES },
  ],
  admin: [
    { label: "nav.admin", path: "/admin", icon: "Shield", permissions: ["platform:manage_users"], roles: ADMIN_ROLES },
    { label: "nav.labs", path: "/labs", icon: "Building2", permissions: ["lab:read"], roles: READONLY_ROLES },
    { label: "nav.stats", path: "/stats", icon: "BarChart3", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "nav.compliance", path: "/compliance", icon: "FileCheck", permissions: ["audit:read"], roles: ADMIN_ROLES },
  ],
  tools: [
    { label: "nav.ai", path: "/ai", icon: "Brain", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "nav.aiPlatform", path: "/ai-platform", icon: "Brain", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "nav.patientCard", path: "/patient-card", icon: "CreditCard", permissions: ["patients:read"], roles: STAFF_ROLES },
    { label: "nav.identity", path: "/identity", icon: "Fingerprint", permissions: ["patients:read"], roles: STAFF_ROLES },
    { label: "nav.tiers", path: "/tiers", icon: "Crown", permissions: ["dashboard:read"], roles: READONLY_ROLES },
  ],
  enterprise: [
    { label: "بوابة عمليات المستشفى", path: "/hospital", icon: "Building", permissions: ["dashboard:read"], roles: HOSPITAL_OPERATIONS_ROLES },
    { label: "nav.edgePlatform", path: "/edge", icon: "Server", permissions: ["system:admin"], roles: ROUTE_ROLE_POLICIES["/edge"] },
    { label: "nav.financial", path: "/financial", icon: "DollarSign", permissions: ["lab:manage"], roles: ADMIN_ROLES },
    { label: "الحوكمة المالية والجاهزية الاستثمارية", path: "/financial-governance", icon: "ShieldCheck", permissions: ["payments:control:read"], roles: FINANCIAL_ROLES },
    { label: "nav.nationalData", path: "/national-data", icon: "BarChart3", permissions: ["patients:read"], roles: ROUTE_ROLE_POLICIES["/national-data"] },
  ],
  niam: [
    { label: "حوكمة الهوية", path: "/niam/governance", icon: "Scale", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "إطار الثقة", path: "/niam/trust", icon: "Shield", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "دورة الحياة", path: "/niam/lifecycle", icon: "UserCircle", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "الاتحاد", path: "/niam/federation", icon: "Globe", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "الشهادات", path: "/niam/certificates", icon: "Certificate", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "سير العمل", path: "/niam/workflows", icon: "Workflow", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "المصادقة التكيفية", path: "/niam/adaptive-auth", icon: "ShieldCheck", permissions: ["system:admin"], roles: ADMIN_ROLES },
  ],
  settings: [
    { label: "nav.profile", path: "/profile", icon: "UserCircle" },
    { label: "nav.settings", path: "/settings", icon: "Settings" },
    { label: "nav.security", path: "/security", icon: "Lock", roles: ADMIN_ROLES },
    { label: "nav.notifications", path: "/notifications", icon: "Bell" },
  ],
  clinical: [
    { label: "الأسس السريرية", path: "/capabilities/clinical-foundation", icon: "Heart", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "إدارة المستندات", path: "/capabilities/document-management", icon: "FileText", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "إدارة الزيارات", path: "/capabilities/encounter-management", icon: "CalendarDays", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "الموافقة الصحية", path: "/capabilities/healthcare-consent", icon: "FileCheck", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "إدارة المزودين", path: "/capabilities/provider-management", icon: "Building2", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "خدمة التقارير", path: "/capabilities/reporting-service", icon: "BarChart3", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "خدمة البحث", path: "/capabilities/search-service", icon: "Search", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "خدمة التخزين", path: "/capabilities/storage-service", icon: "HardDrive", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "محرك سير العمل", path: "/capabilities/workflow-engine", icon: "Workflow", permissions: ["dashboard:read"], roles: READONLY_ROLES }
  ],
  national: [
    { label: "الخلفية الوطنية", path: "/national/background-platform", icon: "Clock", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "الوثائق الوطنية", path: "/national/document-platform", icon: "FileText", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "النظام البيئي", path: "/national/ecosystem", icon: "ShareNetwork", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "بوابة النظام البيئي", path: "/national/ecosystem/gateway", icon: "Router", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "الإشعارات الوطنية", path: "/national/notification-platform", icon: "Bell", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "المراقبة الوطنية", path: "/national/observability", icon: "Eye", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "محرك القواعد", path: "/national/rules-engine", icon: "Braces", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "الجدولة الوطنية", path: "/national/scheduling-platform", icon: "Calendar", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "البحث الوطني", path: "/national/search-platform", icon: "Search", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "محرك المهام", path: "/national/task-engine", icon: "ListChecks", permissions: ["dashboard:read"], roles: ADMIN_ROLES },
    { label: "تشغيل سير العمل", path: "/national/workflow-runtime", icon: "PlayCircle", permissions: ["dashboard:read"], roles: ADMIN_ROLES }
  ],
  systems: [
    { label: "منصة الذكاء الاصطناعي", path: "/ai-fabric", icon: "Brain", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "الطب الحيوي", path: "/biomedical", icon: "Microscope", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "بنك الدم", path: "/blood-bank", icon: "Droplets", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "الشهادات", path: "/certification", icon: "ScrollText", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "منصة المواطن", path: "/citizen-platform", icon: "UserCheck", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "مركز القيادة", path: "/command-center", icon: "Monitor", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "الاستخبارات", path: "/command-intelligence", icon: "BrainCircuit", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "طائرة التحكم", path: "/control-plane", icon: "Gamepad2", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "بوابة الطوارئ والإسعاف والرعاية الحادة", path: "/acute-care-operations", icon: "Ambulance", permissions: ["dashboard:read"], roles: ACUTE_CARE_OPERATIONS_ROLES },
    { label: "البيانات الصحية", path: "/health-data", icon: "Database", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "التكامل", path: "/integration", icon: "Cable", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "منظومة القدرات الصحية", path: "/health-ecosystem", icon: "HeartPulse", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "النواة", path: "/kernel", icon: "Cpu", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "دورة حياة المنصة", path: "/lifecycle-platform", icon: "RefreshCw", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "الصيدلة", path: "/pharmacy", icon: "Pill", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "إدارة الصيدلية والأدوية", path: "/pharmacy-operations", icon: "Pill", permissions: ["dashboard:read"], roles: PHARMACY_OPERATIONS_ROLES },
    { label: "عمليات الأشعة والتصوير", path: "/radiology-operations", icon: "Activity", permissions: ["dashboard:read"], roles: RADIOLOGY_OPERATIONS_ROLES },
    { label: "بوابة العيادة الطبية", path: "/clinic-operations", icon: "Stethoscope", permissions: ["dashboard:read"], roles: CLINIC_OPERATIONS_ROLES },
    { label: "بوابة عمليات المستشفى", path: "/hospital-operations", icon: "Building", permissions: ["dashboard:read"], roles: HOSPITAL_OPERATIONS_ROLES },
    { label: "إدارة الفوترة والتأمين", path: "/billing-insurance", icon: "ReceiptText", permissions: ["dashboard:read"], roles: READONLY_ROLES },
    { label: "مركز ربط الأجهزة", path: "/device-integration", icon: "Cable", permissions: ["lab:read"], roles: READONLY_ROLES, institutionalOnly: true },
    { label: "المنصة التجريبية", path: "/pilot-platform", icon: "FlaskConical", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "المنصة", path: "/platform", icon: "Layers", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "الصحة العامة", path: "/public-health", icon: "Activity", permissions: ["system:admin"], roles: ADMIN_ROLES },
    { label: "التوافق الصحي FHIR", path: "/fhir", icon: "Share2", permissions: ["system:admin"], roles: ADMIN_ROLES },
  ],
};
