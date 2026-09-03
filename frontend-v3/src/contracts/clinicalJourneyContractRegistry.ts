export type WorkstreamId =
  | "citizen-identity"
  | "doctor-workspace"
  | "organization"
  | "laboratory"
  | "pharmacy"
  | "radiology"
  | "clinic"
  | "hospital"
  | "acute-care"
  | "design-system"
  | "screen-gallery"
  | "master-golden-path";

export type WorkstreamStatus = "implemented-safely" | "partial" | "backend-blocked" | "external-input-blocked" | "remote-blocked";
export type RequirementKind = "backend" | "frontend" | "security" | "external" | "remote";
export type RequirementStatus = "met" | "missing" | "blocked";

export interface ContractRequirement {
  id: string;
  label: string;
  kind: RequirementKind;
  status: RequirementStatus;
}

export interface WorkstreamGap {
  id: WorkstreamId;
  title: string;
  status: WorkstreamStatus;
  currentState: string;
  blocker: string;
  safeNextAction: string;
  requirements: readonly ContractRequirement[];
}

export const PREVIOUS_WORKSTREAMS: readonly WorkstreamGap[] = [
  {
    id: "citizen-identity",
    title: "المواطن والهوية",
    status: "partial",
    currentState: "مركز الهوية والمساحات والموافقات والسحب الخادمي مع Demo معزول.",
    blocker: "OTP والجلسات والأجهزة والتحقق وHealth Record Discovery تحتاج عقود self-service وأدلة احتفاظ وخصوصية وتكاملات مفوضة.",
    safeNextAction: "إضافة عقود typed واختبارات حالات دون إنشاء هوية أو verification من الواجهة.",
    requirements: [
      { id: "citizen-session", label: "Self-session/device contract", kind: "backend", status: "missing" },
      { id: "citizen-verification", label: "Verification evidence and retention", kind: "security", status: "missing" },
      { id: "citizen-identity-integration", label: "Government identity integration", kind: "external", status: "blocked" },
    ],
  },
  {
    id: "doctor-workspace",
    title: "الطبيب",
    status: "partial",
    currentState: "Workspace خادمي وقراءة patients/orders محدودة عبر canonical gateway.",
    blocker: "Appointment وPatient Access وEncounter وClinical Note وLab Order وResult Review وPrescription وReferral تحتاج عقود كتابة سياقية.",
    safeNextAction: "تثبيت state-machine types وnegative authorization fixtures قبل أي write UI.",
    requirements: [
      { id: "doctor-access", label: "Object-level patient access", kind: "backend", status: "missing" },
      { id: "doctor-encounter", label: "Encounter/note lifecycle", kind: "backend", status: "missing" },
      { id: "doctor-write-safety", label: "If-Match, idempotency, audit", kind: "security", status: "missing" },
    ],
  },
  {
    id: "organization",
    title: "المؤسسة الصحية",
    status: "partial",
    currentState: "عرض workspaces/memberships المعادة من الخادم مع Demo منفصل.",
    blocker: "الترخيص والفروع والدعوات وتعيين الأدوار والأجهزة والمالية والجودة قرارات organization/IAM خادمية.",
    safeNextAction: "توثيق action matrix واختبارات cross-tenant؛ عدم فتح CRUD محلي.",
    requirements: [{ id: "organization-iam", label: "Ownership, membership and scoped IAM contract", kind: "backend", status: "missing" }],
  },
  {
    id: "laboratory",
    title: "المختبر",
    status: "backend-blocked",
    currentState: "Demo كامل وقراءة orders محدودة بعد تفعيل workspace.",
    blocker: "Specimen وaccession وbarcode وanalyzer وQC وvalidation وrelease وcritical escalation غير مقبولة في frontend boundary.",
    safeNextAction: "اختبارات انتقالات العينة والنتيجة مع fixtures اصطناعية فقط.",
    requirements: [
      { id: "lab-specimen", label: "Specimen chain-of-custody contract", kind: "backend", status: "missing" },
      { id: "lab-result", label: "Senior validation and release contract", kind: "security", status: "missing" },
      { id: "lab-instrument", label: "LIS/analyzer integration", kind: "external", status: "blocked" },
    ],
  },
  {
    id: "pharmacy",
    title: "الصيدلية",
    status: "backend-blocked",
    currentState: "Demo read-only وقراءة summary/catalog/stock محدودة.",
    blocker: "Verification وinteraction/allergy checks وbatch ledger وpartial dispensing وcontrolled medicines تحتاج عقداً سريرياً/مخزنياً/مالياً.",
    safeNextAction: "معاينة حالات verification وrejection وpartial دون زر صرف حي.",
    requirements: [
      { id: "pharmacy-prescription", label: "Prescription verification contract", kind: "backend", status: "missing" },
      { id: "pharmacy-ledger", label: "Batch/expiry/idempotent inventory ledger", kind: "security", status: "missing" },
    ],
  },
  {
    id: "radiology",
    title: "الأشعة والتصوير",
    status: "backend-blocked",
    currentState: "Demo ومسح metadata محدود دون صور أو تقارير حية.",
    blocker: "RIS/PACS/DICOM وreport lifecycle وverification/release وsharing تحتاج تكاملاً وعزل object-level.",
    safeNextAction: "إبقاء metadata gate واختبار منع URLs والتقارير الوهمية.",
    requirements: [
      { id: "radiology-order", label: "Imaging order/study/report contract", kind: "backend", status: "missing" },
      { id: "radiology-pacs", label: "RIS/PACS/DICOM integration", kind: "external", status: "blocked" },
    ],
  },
  {
    id: "clinic",
    title: "العيادة والـEncounter",
    status: "backend-blocked",
    currentState: "Demo وقراءات patients/orders المحدودة.",
    blocker: "Appointment/queue/check-in/Encounter/diagnosis/orders/prescription/referral غير متاحة بعقد workspace-scoped.",
    safeNextAction: "تثبيت contract gate وحالات 401/403/409/422/503 دون clinical writes.",
    requirements: [{ id: "clinic-encounter", label: "Clinic encounter lifecycle contract", kind: "backend", status: "missing" }],
  },
  {
    id: "hospital",
    title: "المستشفى",
    status: "backend-blocked",
    currentState: "Hospital Operations Demo وpatients/orders فقط، و`/hospital` alias آمن.",
    blocker: "Broad `/hospital/*` غير workspace-scoped للواجهة؛ admission وbeds وnursing وOR وICU وblood وdischarge محجوبة.",
    safeNextAction: "تصميم occupancy/admission/bed history/care-team contracts محدودة قبل أي route حي.",
    requirements: [{ id: "hospital-scoped", label: "Facility/ward-scoped hospital operations contracts", kind: "backend", status: "missing" }],
  },
  {
    id: "acute-care",
    title: "الطوارئ والإسعاف والرعاية الحادة",
    status: "backend-blocked",
    currentState: "Demo اصطناعي وaliases آمنة لـ`/ems` و`/critical-care`.",
    blocker: "Emergency/Break-Glass/Dispatch/GPS/ePCR/ICU telemetry تحتاج سبباً ونطاقاً وتدقيقاً وانتهاءً وتكاملاً مفوضاً.",
    safeNextAction: "الحفاظ على gates وإضافة negative tests للـbreak-glass والـtenant isolation.",
    requirements: [{ id: "acute-break-glass", label: "Break-glass and EMS authorization contract", kind: "security", status: "missing" }],
  },
  {
    id: "design-system",
    title: "Unified Clinical Journey & Design System",
    status: "implemented-safely",
    currentState: "Tokens وclinical primitives وshell وassistant وRTL/accessibility states مطبقة.",
    blocker: "Parity الكامل للترجمات والمنصات والـvisual regression والـproduction telemetry يحتاج مراجعة وبيئات إضافية.",
    safeNextAction: "إكمال resource review واختبارات visual/accessibility على Web/Mobile/Desktop.",
    requirements: [
      { id: "design-a11y", label: "Automated accessibility coverage", kind: "frontend", status: "met" },
      { id: "design-platform-parity", label: "Web/Mobile/Desktop parity", kind: "frontend", status: "missing" },
    ],
  },
  {
    id: "screen-gallery",
    title: "Screen-by-Screen",
    status: "implemented-safely",
    currentState: "معرض تفاعلي اصطناعي lazy-loaded مع gated states.",
    blocker: "ربط كل شاشة بـbackend وE2E عبر المنصات يحتاج عقوداً وبيئات اختبار اصطناعية.",
    safeNextAction: "استخدام المعرض كمرجع UX وعدم تسميته واجهة إنتاجية.",
    requirements: [{ id: "screen-e2e", label: "Cross-platform synthetic E2E", kind: "frontend", status: "missing" }],
  },
  {
    id: "master-golden-path",
    title: "Frontend Master وGolden Path",
    status: "partial",
    currentState: "Domain gates وGolden Path Readiness وroute/data-source governance مطبقة.",
    blocker: "Appointment → Encounter → Lab → Result → Review → Citizen → Share → Revoke → Audit لا تزال بلا E2E خادمي كامل.",
    safeNextAction: "تنفيذ العقود بالترتيب وإبقاء عبارة `GOLDEN PATH PASSED` محجوبة حتى اكتمال الأدلة.",
    requirements: [
      { id: "golden-backend", label: "Cross-domain backend contracts", kind: "backend", status: "missing" },
      { id: "golden-remote", label: "Remote CI and staging evidence", kind: "remote", status: "blocked" },
    ],
  },
];

export type GoldenPathStageState = "loaded" | "partial" | "maintenance";

export interface GoldenPathStage {
  id: string;
  label: string;
  state: GoldenPathStageState;
  detail: string;
}

export const GOLDEN_PATH_STAGES: readonly GoldenPathStage[] = [
  { id: "identity", label: "Identity", state: "loaded", detail: "جلسة وملف هوية معادان من الخادم" },
  { id: "workspace", label: "Workspace", state: "loaded", detail: "اختيار المساحة يمر عبر switchWorkspace" },
  { id: "access", label: "Patient Access", state: "partial", detail: "قراءات محدودة فقط عند تحقق السياق والعلاقة" },
  { id: "appointment", label: "Appointment", state: "maintenance", detail: "يحتاج عقد دورة الموعد ومنع التكرار" },
  { id: "encounter", label: "Encounter", state: "maintenance", detail: "يحتاج state machine وتوقيعاً وتعديلات مدققة" },
  { id: "lab-order", label: "Lab Order", state: "maintenance", detail: "يحتاج Patient + Encounter + Facility + Idempotency" },
  { id: "specimen", label: "Specimen", state: "maintenance", detail: "لا جمع أو رفض أو حذف قبل عقد العينة" },
  { id: "result", label: "Result", state: "maintenance", detail: "لا تحقق أو إطلاق قبل عقد النتيجة" },
  { id: "review", label: "Doctor Review", state: "maintenance", detail: "لا acknowledgment أو clinical action من الواجهة" },
  { id: "citizen-result", label: "Citizen Access", state: "partial", detail: "يعتمد على حالة الإطلاق والنطاق المسموح" },
  { id: "sharing", label: "Sharing / Revoke", state: "partial", detail: "السحب المتاح يمر عبر عقد الخادم؛ الإنشاء محكوم" },
  { id: "audit", label: "Audit", state: "maintenance", detail: "التدقيق الحي لا يفتح من هذا المسار" },
];

export function canAdvertiseCompleted(workstream: WorkstreamGap): boolean {
  return workstream.status === "implemented-safely" && workstream.requirements.every((requirement) => requirement.status === "met");
}

export function summarizeRemainingWork(): { total: number; complete: number; partial: number; blocked: number } {
  return PREVIOUS_WORKSTREAMS.reduce(
    (summary, workstream) => {
      summary.total += 1;
      if (canAdvertiseCompleted(workstream)) summary.complete += 1;
      else if (workstream.status === "partial") summary.partial += 1;
      else summary.blocked += 1;
      return summary;
    },
    { total: 0, complete: 0, partial: 0, blocked: 0 },
  );
}
