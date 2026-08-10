import type { UserRole } from "@/types";

export const DEMO_PROFILE_IDS = ["citizen", "doctor", "lab_staff", "nurse", "health_admin"] as const;
export type DemoProfileId = (typeof DEMO_PROFILE_IDS)[number];

export interface DemoProfile {
  id: DemoProfileId;
  labelAr: string;
  labelEn: string;
  descriptionAr: string;
  descriptionEn: string;
  displayNameAr: string;
  displayNameEn: string;
  role: UserRole;
  icon: string;
}

/**
 * Demo profiles are presentation-only previews. Each one maps to an existing
 * application role so that no privileged or invented role is introduced.
 * The demo session is never treated as a security credential.
 */
export const DEMO_PROFILES: Record<DemoProfileId, DemoProfile> = {
  citizen: {
    id: "citizen",
    labelAr: "مواطن",
    labelEn: "Citizen",
    descriptionAr: "استعراض لوحة المواطن والخدمات والمواعيد",
    descriptionEn: "Citizen dashboard, services and appointments preview",
    displayNameAr: "مواطن تجريبي",
    displayNameEn: "Demo Citizen",
    role: "citizen",
    icon: "User",
  },
  doctor: {
    id: "doctor",
    labelAr: "طبيب",
    labelEn: "Doctor",
    descriptionAr: "استعراض رحلة المريض والمواعيد والنظرة السريرية",
    descriptionEn: "Patient journey, appointments and clinical overview preview",
    displayNameAr: "طبيب تجريبي",
    displayNameEn: "Demo Physician",
    role: "doctor",
    icon: "Stethoscope",
  },
  lab_staff: {
    id: "lab_staff",
    labelAr: "موظف مختبر",
    labelEn: "Laboratory Professional",
    descriptionAr: "استعراض لوحة المختبر والطلبات والعينات والنتائج",
    descriptionEn: "Laboratory dashboard, orders, specimens and results preview",
    displayNameAr: "موظف مختبر تجريبي",
    displayNameEn: "Demo Lab Professional",
    role: "lab_staff",
    icon: "TestTube",
  },
  nurse: {
    id: "nurse",
    labelAr: "ممرض",
    labelEn: "Nurse",
    descriptionAr: "استعراض لوحة التمريض وتدفق المرضى",
    descriptionEn: "Nursing dashboard and patient flow preview",
    displayNameAr: "ممرض تجريبي",
    displayNameEn: "Demo Nurse",
    role: "nurse",
    icon: "HeartPulse",
  },
  health_admin: {
    id: "health_admin",
    labelAr: "إدارة صحية",
    labelEn: "Health Administration",
    descriptionAr: "استعراض لوحة الإدارة الصحية والإحصائيات",
    descriptionEn: "Health administration dashboard and statistics preview",
    displayNameAr: "مدير صحي تجريبي",
    displayNameEn: "Demo Health Administrator",
    role: "admin",
    icon: "Building2",
  },
};

export function isDemoProfileId(value: string): value is DemoProfileId {
  return (DEMO_PROFILE_IDS as readonly string[]).includes(value);
}

export function getDemoProfile(id: DemoProfileId): DemoProfile {
  return DEMO_PROFILES[id]!;
}
