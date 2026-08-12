export const roleLabels = {
  patient: { ar: "المواطن / المريض", en: "Citizen / Patient" },
  lab_staff: { ar: "طاقم المختبر والمؤسسة", en: "Laboratory & Clinical Staff" },
  physician: { ar: "الطبيب / الأخصائي", en: "Physician & Specialist" },
  institution_admin: { ar: "مدير المؤسسة الصحية", en: "Healthcare Institution Admin" },
  system_admin: { ar: "مدير النظام الوطني", en: "National System Admin" },
} as const;

export const permissionCatalog = {
  patientRead: "patient.read",
  patientCreate: "patient.create",
  patientUpdate: "patient.update",
  medicalRecordRead: "medical_record.read",
  labOrderRead: "lab_order.read",
  labOrderCreate: "lab_order.create",
  labOrderUpdate: "lab_order.update",
  sampleRead: "sample.read",
  sampleReceive: "sample.receive",
  sampleVerify: "sample.verify",
  specimenProcess: "specimen.process",
  resultRead: "result.read",
  resultEnter: "result.enter",
  resultReview: "result.review",
  resultRelease: "result.release",
  hospitalAdt: "hospital.adt",
  clinicConsult: "clinic.consult",
  pharmacyDispense: "pharmacy.dispense",
  radiologyView: "radiology.view",
  emergencyTriage: "emergency.triage",
  publicHealthReport: "public_health.report",
  criticalAlertRead: "critical_alert.read",
  criticalAlertAcknowledge: "critical_alert.acknowledge",
  notificationRead: "notification.read",
  notificationManage: "notification.manage",
  taskRead: "task.read",
  reportRead: "report.read",
  auditRead: "audit.read",
  userManage: "user.manage",
  laboratoryManage: "laboratory.manage",
  organizationManage: "organization.manage",
} as const;

export type LisPermission = (typeof permissionCatalog)[keyof typeof permissionCatalog];

export const rolePermissions: Record<keyof typeof roleLabels, readonly LisPermission[]> = {
  patient: [permissionCatalog.patientRead, permissionCatalog.medicalRecordRead, permissionCatalog.labOrderRead, permissionCatalog.resultRead, permissionCatalog.notificationRead, permissionCatalog.taskRead],
  lab_staff: [permissionCatalog.patientRead, permissionCatalog.patientUpdate, permissionCatalog.labOrderRead, permissionCatalog.sampleRead, permissionCatalog.sampleReceive, permissionCatalog.sampleVerify, permissionCatalog.specimenProcess, permissionCatalog.resultRead, permissionCatalog.resultEnter, permissionCatalog.radiologyView, permissionCatalog.criticalAlertRead, permissionCatalog.criticalAlertAcknowledge, permissionCatalog.notificationRead, permissionCatalog.taskRead, permissionCatalog.reportRead],
  physician: [permissionCatalog.patientRead, permissionCatalog.medicalRecordRead, permissionCatalog.labOrderRead, permissionCatalog.labOrderCreate, permissionCatalog.labOrderUpdate, permissionCatalog.resultRead, permissionCatalog.resultReview, permissionCatalog.resultRelease, permissionCatalog.hospitalAdt, permissionCatalog.clinicConsult, permissionCatalog.emergencyTriage, permissionCatalog.criticalAlertRead, permissionCatalog.notificationRead, permissionCatalog.taskRead],
  institution_admin: [permissionCatalog.patientRead, permissionCatalog.patientCreate, permissionCatalog.patientUpdate, permissionCatalog.medicalRecordRead, permissionCatalog.labOrderRead, permissionCatalog.sampleRead, permissionCatalog.resultRead, permissionCatalog.hospitalAdt, permissionCatalog.clinicConsult, permissionCatalog.pharmacyDispense, permissionCatalog.radiologyView, permissionCatalog.emergencyTriage, permissionCatalog.publicHealthReport, permissionCatalog.criticalAlertRead, permissionCatalog.notificationRead, permissionCatalog.notificationManage, permissionCatalog.taskRead, permissionCatalog.reportRead, permissionCatalog.auditRead, permissionCatalog.userManage, permissionCatalog.laboratoryManage],
  system_admin: Object.values(permissionCatalog),
};

export const workspaceCatalog = [
  {
    id: "citizen",
    label: { ar: "صحتي الوطنية", en: "My Health" },
    description: { ar: "ملفك الصحي الموحد ونتائجك والخدمات الساندة", en: "Unified health record, results, and services" },
    roles: ["patient"],
    accent: "teal",
    capabilities: [permissionCatalog.patientRead, permissionCatalog.resultRead, permissionCatalog.notificationRead],
  },
  {
    id: "clinical",
    label: { ar: "العيادات والتشخيص", en: "Outpatient & Clinics" },
    description: { ar: "المواعيد، الاستشارات الطبية، والوصفات الإلكترونية", en: "Consultations, notes, and e-prescriptions" },
    roles: ["physician", "institution_admin", "system_admin"],
    accent: "blue",
    capabilities: [permissionCatalog.patientRead, permissionCatalog.clinicConsult, permissionCatalog.labOrderCreate, permissionCatalog.resultRead],
  },
  {
    id: "hospital",
    label: { ar: "المستشفيات والتمريض", en: "Hospital & Inpatient" },
    description: { ar: "الأقسام، الأسرّة، الدخول والتحويل والتمريض", en: "ADT, ward rounds, and inpatient nursing" },
    roles: ["physician", "institution_admin", "system_admin"],
    accent: "violet",
    capabilities: [permissionCatalog.hospitalAdt, permissionCatalog.medicalRecordRead],
  },
  {
    id: "laboratory",
    label: { ar: "المختبرات الطبية", en: "Laboratories (LIS)" },
    description: { ar: "العينات، الفحوصات، النتائج، ومراقبة الجودة", en: "Specimens, test execution, results, and QC" },
    roles: ["lab_staff", "physician", "institution_admin", "system_admin"],
    accent: "amber",
    capabilities: [permissionCatalog.sampleReceive, permissionCatalog.specimenProcess, permissionCatalog.resultEnter, permissionCatalog.resultReview],
  },
  {
    id: "pharmacy",
    label: { ar: "الصيدلة والإمداد", en: "Pharmacy & Supply" },
    description: { ar: "كتالوج الأدوية، صرف الوصفات، والمخزون الطبي", en: "Drug catalogs, prescription dispensing, inventory" },
    roles: ["institution_admin", "system_admin"],
    accent: "teal",
    capabilities: [permissionCatalog.pharmacyDispense],
  },
  {
    id: "radiology",
    label: { ar: "الأشعة والصور الطبية", en: "Radiology & PACS" },
    description: { ar: "طلبات الأشعة، تقارير التصوير، وDICOM", en: "Imaging orders, reports, and PACS metadata" },
    roles: ["lab_staff", "physician", "institution_admin", "system_admin"],
    accent: "slate",
    capabilities: [permissionCatalog.radiologyView],
  },
  {
    id: "emergency",
    label: { ar: "الطوارئ والفرز", en: "Emergency & Triage" },
    description: { ar: "إدارة الإصابات، الفرز السريع، والتنبيهات الحرجة", en: "Trauma triage, fast-track intake, critical alerts" },
    roles: ["physician", "institution_admin", "system_admin"],
    accent: "rose",
    capabilities: [permissionCatalog.emergencyTriage, permissionCatalog.criticalAlertRead],
  },
  {
    id: "public_health",
    label: { ar: "الصحة العامة", en: "Public Health" },
    description: { ar: "رصد الأوبئة، التقارير الوطنية، والمؤشرات الوبائية", en: "Epidemiological surveillance and national reporting" },
    roles: ["institution_admin", "system_admin"],
    accent: "blue",
    capabilities: [permissionCatalog.publicHealthReport, permissionCatalog.reportRead],
  },
  {
    id: "facility",
    label: { ar: "إدارة المؤسسة", en: "Facility Administration" },
    description: { ar: "إدارة الموظفين، الصلاحيات، والموارد للقطاع العام والخاص", en: "Staff, permissions, and institutional resources" },
    roles: ["institution_admin", "system_admin"],
    accent: "violet",
    capabilities: [permissionCatalog.userManage, permissionCatalog.laboratoryManage, permissionCatalog.reportRead, permissionCatalog.auditRead],
  },
  {
    id: "governance",
    label: { ar: "الحوكمة الوطنية", en: "National Governance" },
    description: { ar: "الرقابة المركزية، السياسات، وتكامل القطاعات الصحية", en: "Central oversight, policies, and sector integration" },
    roles: ["system_admin"],
    accent: "slate",
    capabilities: [permissionCatalog.organizationManage, permissionCatalog.auditRead, permissionCatalog.reportRead],
  },
] as const;

export type LisRole = keyof typeof roleLabels;
export type WorkspaceId = (typeof workspaceCatalog)[number]["id"];
export type OrganizationContext = {
  institutionId: number | null;
  laboratoryId: number | null;
  role: LisRole;
};

export const orderTransitions = {
  draft: ["submitted", "cancelled"],
  submitted: ["sample_pending", "cancelled"],
  sample_pending: ["in_progress", "cancelled"],
  in_progress: ["result_pending_review", "cancelled"],
  result_pending_review: ["completed"],
  completed: [],
  cancelled: [],
} as const;

export const sampleTransitions = {
  expected: ["received", "rejected"],
  received: ["verified", "rejected"],
  verified: ["processing"],
  processing: ["completed", "rejected"],
  rejected: [],
  completed: [],
} as const;

export const resultTransitions = {
  not_started: ["entered"],
  entered: ["pending_review", "rejected"],
  pending_review: ["approved", "rejected"],
  approved: ["released"],
  released: [],
  rejected: ["entered"],
} as const;

export function discoverWorkspaces(roles: readonly string[]) {
  return workspaceCatalog.filter((workspace) => workspace.roles.some((role) => roles.includes(role)));
}

export function permissionsForRoles(roles: readonly string[]) {
  return Array.from(new Set(roles.flatMap((role) => rolePermissions[role as LisRole] ?? []))) as LisPermission[];
}

export function hasPermission(roles: readonly string[], permission: LisPermission) {
  return permissionsForRoles(roles).includes(permission);
}

export function canUseWorkspace(workspaceId: string, roles: readonly string[]) {
  return discoverWorkspaces(roles).some((workspace) => workspace.id === workspaceId);
}

export function canUsePermissionInWorkspace(workspaceId: string, roles: readonly string[], permission: LisPermission) {
  return canUseWorkspace(workspaceId, roles) && hasPermission(roles, permission);
}
