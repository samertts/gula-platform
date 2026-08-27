import type { UserRole } from "@/types";

/**
 * Frontend defense-in-depth policy. The backend remains the authoritative
 * authorization boundary; these groups only prevent dead-end links and
 * accidental UI exposure before a request is made.
 */
export const ADMIN_ROLES = [
  "master_admin",
  "admin",
  "lab_admin",
  "ministry_admin",
  "province_admin",
] as const satisfies readonly UserRole[];

export const STAFF_ROLES = [
  ...ADMIN_ROLES,
  "doctor",
  "staff",
  "lab_staff",
  "technician",
] as const satisfies readonly UserRole[];

export const READONLY_ROLES = [
  ...ADMIN_ROLES,
  "doctor",
  "staff",
  "lab_staff",
  "demo_viewer",
] as const satisfies readonly UserRole[];

export const LAB_ROLES = [
  "master_admin",
  "admin",
  "lab_admin",
  "staff",
  "lab_staff",
] as const satisfies readonly UserRole[];

export const LAB_OPERATIONS_ROLES = [
  ...LAB_ROLES,
  "demo_viewer",
] as const satisfies readonly UserRole[];

export const PHARMACY_OPERATIONS_ROLES = [
  ...ADMIN_ROLES,
  "staff",
  "cashier",
  "demo_viewer",
] as const satisfies readonly UserRole[];

export const RADIOLOGY_OPERATIONS_ROLES = [
  ...ADMIN_ROLES,
  "doctor",
  "staff",
  "technician",
  "demo_viewer",
] as const satisfies readonly UserRole[];

export const CLINIC_OPERATIONS_ROLES = [
  ...ADMIN_ROLES,
  "doctor",
  "staff",
  "technician",
  "demo_viewer",
] as const satisfies readonly UserRole[];

export const HOSPITAL_OPERATIONS_ROLES = [
  ...ADMIN_ROLES,
  "doctor",
  "staff",
  "lab_staff",
  "technician",
  "demo_viewer",
] as const satisfies readonly UserRole[];

export const ORGANIZATION_ROLES = [
  ...READONLY_ROLES,
  "technician",
] as const satisfies readonly UserRole[];

export const FINANCIAL_ROLES = [
  "master_admin",
  "admin",
  "lab_admin",
  "finance_controller",
  "refund_reviewer",
  "reconciler",
  "finance_auditor",
  "finance_operator",
  "cashier",
] as const satisfies readonly UserRole[];

export type RouteRolePolicy = readonly UserRole[];

export const ROUTE_ROLE_POLICIES = {
  "/patients": STAFF_ROLES,
  "/patient-management": READONLY_ROLES,
  "/organization-workspace": ORGANIZATION_ROLES,
  "/lab-operations": LAB_OPERATIONS_ROLES,
  "/orders": STAFF_ROLES,
  "/reports": READONLY_ROLES,
  "/results": STAFF_ROLES,
  "/samples": LAB_ROLES,
  "/labs": READONLY_ROLES,
  "/alerts": READONLY_ROLES,
  "/ai": READONLY_ROLES,
  "/ai-platform": READONLY_ROLES,
  "/stats": READONLY_ROLES,
  "/qc": READONLY_ROLES,
  "/patient-card": STAFF_ROLES,
  "/patient-visit/readiness": READONLY_ROLES,
  "/identity": STAFF_ROLES,
  "/tiers": READONLY_ROLES,
  "/compliance": ADMIN_ROLES,
  "/security": ADMIN_ROLES,
  "/admin": ADMIN_ROLES,
  "/admin/labs": ADMIN_ROLES,
  "/admin/users": ADMIN_ROLES,
  "/admin/audit": ADMIN_ROLES,
  "/fhir": ADMIN_ROLES,
  "/ehr": ADMIN_ROLES,
  "/hospital": HOSPITAL_OPERATIONS_ROLES,
  "/edge": ["master_admin", "admin"] as const satisfies readonly UserRole[],
  "/financial": ADMIN_ROLES,
  "/financial-governance": FINANCIAL_ROLES,
  "/national-data": [
    "master_admin",
    "ministry_admin",
    "province_admin",
  ] as const satisfies readonly UserRole[],
  "/niam/governance": ADMIN_ROLES,
  "/niam/trust": ADMIN_ROLES,
  "/niam/lifecycle": ADMIN_ROLES,
  "/niam/federation": ADMIN_ROLES,
  "/niam/certificates": ADMIN_ROLES,
  "/niam/workflows": ADMIN_ROLES,
  "/niam/adaptive-auth": ADMIN_ROLES,
  "/ai-fabric": ADMIN_ROLES,
  "/biomedical": ADMIN_ROLES,
  "/blood-bank": ADMIN_ROLES,
  "/capabilities/clinical-foundation": READONLY_ROLES,
  "/capabilities/document-management": READONLY_ROLES,
  "/capabilities/encounter-management": READONLY_ROLES,
  "/capabilities/healthcare-consent": READONLY_ROLES,
  "/capabilities/provider-management": READONLY_ROLES,
  "/capabilities/reporting-service": READONLY_ROLES,
  "/capabilities/search-service": READONLY_ROLES,
  "/capabilities/storage-service": READONLY_ROLES,
  "/capabilities/workflow-engine": READONLY_ROLES,
  "/certification": ADMIN_ROLES,
  "/citizen": ["citizen"] as const satisfies readonly UserRole[],
  "/citizen-platform": ADMIN_ROLES,
  "/command-center": ADMIN_ROLES,
  "/command-intelligence": ADMIN_ROLES,
  "/control-plane": ADMIN_ROLES,
  "/critical-care": ADMIN_ROLES,
  "/ems": ADMIN_ROLES,
  "/health-data": ADMIN_ROLES,
  "/integration": ADMIN_ROLES,
  "/integration/connectors": ADMIN_ROLES,
  "/health-ecosystem": READONLY_ROLES,
  "/kernel": ADMIN_ROLES,
  "/lifecycle-platform": ADMIN_ROLES,
  "/national/background-platform": ADMIN_ROLES,
  "/national/document-platform": ADMIN_ROLES,
  "/national/ecosystem": ADMIN_ROLES,
  "/national/ecosystem/gateway": ADMIN_ROLES,
  "/national/notification-platform": ADMIN_ROLES,
  "/national/observability": ADMIN_ROLES,
  "/national/rules-engine": ADMIN_ROLES,
  "/national/scheduling-platform": ADMIN_ROLES,
  "/national/search-platform": ADMIN_ROLES,
  "/national/task-engine": ADMIN_ROLES,
  "/national/workflow-runtime": ADMIN_ROLES,
  "/pharmacy": ADMIN_ROLES,
  "/pharmacy-operations": PHARMACY_OPERATIONS_ROLES,
  "/radiology-operations": RADIOLOGY_OPERATIONS_ROLES,
  "/clinic-operations": CLINIC_OPERATIONS_ROLES,
  "/hospital-operations": HOSPITAL_OPERATIONS_ROLES,
  "/billing-insurance": READONLY_ROLES,
  "/device-integration": READONLY_ROLES,
  "/pilot-platform": ADMIN_ROLES,
  "/platform": ADMIN_ROLES,
  "/public-health": ADMIN_ROLES,
} as const satisfies Record<string, RouteRolePolicy>;

export function getRouteRoles(path: string): RouteRolePolicy | undefined {
  return ROUTE_ROLE_POLICIES[path as keyof typeof ROUTE_ROLE_POLICIES];
}
