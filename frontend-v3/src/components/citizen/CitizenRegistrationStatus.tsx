import { AdaptiveStatus } from "@/components/accessibility/AdaptiveComponents";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";

export interface RegistrationStatusPayload {
  case_reference: string;
  lifecycle_state: string;
  verification_state: string;
  can_access_medical_data: boolean;
  next_step: string;
  requires_in_person_review: boolean;
  identity_submitted: boolean;
  health_identity_approved: boolean;
  official_verification: boolean;
  synthetic: boolean;
  notice: string;
}

const LIFECYCLE_LABELS: Record<string, string> = {
  INITIAL_ACCOUNT_CREATED: "تم إنشاء الحساب الأولي",
  CONTACT_VERIFIED: "تم التحقق من وسيلة التواصل",
  NATIONAL_IDENTITY_SUBMITTED: "تم تقديم بيانات الهوية الوطنية",
  NATIONAL_IDENTITY_PENDING_REVIEW: "قيد المراجعة الحضورية",
  HEALTH_IDENTITY_APPROVED: "تمت الموافقة على الهوية الصحية",
  SERVICE_ACTIVE: "الخدمة فعّالة",
  REJECTED: "مرفوض",
  SUSPENDED: "موقوف",
};

const VERIFICATION_LABELS: Record<string, string> = {
  UNVERIFIED: "غير موثّق",
  PENDING_REVIEW: "قيد المراجعة",
  VERIFIED: "موثّق",
};

const NEXT_STEP_LABELS: Record<string, string> = {
  verify_contact: "الخطوة التالية: التحقق من رقم الهاتف أو وسيلة التواصل.",
  submit_identity: "الخطوة التالية: تقديم بيانات الوثيقة الأصلية للمراجعة.",
  await_in_person_review: "الخطوة التالية: انتظار مراجعة مختصة في موقع معتمد.",
  activation_pending_owner_approval: "الخطوة التالية: تفعيل الخدمة بعد اعتماد الجهة المخولة.",
  none: "لا توجد خطوة مطلوبة حالياً.",
  contact_support: "الخطوة التالية: التواصل مع الدعم.",
};

const SYNTHETIC_NOTICE =
  "بيانات تجريبية داخل بيئة معزولة. هذه الحالة ليست تحققاً حكومياً ولا تمنح الوصول إلى البيانات الطبية.";

export function CitizenRegistrationStatus({ status }: { status: RegistrationStatusPayload }) {
  const lifecycleLabel = LIFECYCLE_LABELS[status.lifecycle_state] ?? "حالة غير معروفة";
  const verificationLabel = VERIFICATION_LABELS[status.verification_state] ?? "حالة غير معروفة";
  const nextStep = NEXT_STEP_LABELS[status.next_step] ?? NEXT_STEP_LABELS.contact_support;
  const medicalLabel = status.can_access_medical_data
    ? "الوصول للبيانات الطبية: مفعّل"
    : "الوصول للبيانات الطبية: غير مفعّل";

  return (
    <section dir="rtl" lang="ar" aria-label="حالة طلب إنشاء الحساب">
      <Card>
        <CardHeader>
          <CardTitle>حالة طلب إنشاء الحساب</CardTitle>
          <CardDescription>عرض آمن لحالة الطلب داخل البيئة التجريبية</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{lifecycleLabel}</Badge>
            <Badge variant="secondary">حالة التحقق: {verificationLabel}</Badge>
            {status.requires_in_person_review && (
              <Badge variant="warning">مراجعة حضورية مطلوبة</Badge>
            )}
          </div>
          <AdaptiveStatus
            state={status.can_access_medical_data ? "enabled" : "permission_denied"}
            label={medicalLabel}
            description="لا تُمنح الصلاحية قبل استكمال التحقق واعتماد الجهة المخولة."
          />
          <p role="status" aria-live="polite" className="text-sm font-semibold">
            {nextStep}
          </p>
          <p className="text-xs leading-5 text-muted-foreground">{SYNTHETIC_NOTICE}</p>
          <p className="text-xs text-muted-foreground" aria-label="رقم الحالة التجريبي">
            رقم الحالة: {status.case_reference}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}

// Demo-only synthetic payload that mirrors the backend projection vocabulary.
// It is not runtime-bound to an API and makes no government verification claim.
export const SYNTHETIC_REGISTRATION_STATUS: RegistrationStatusPayload = {
  case_reference: "CASE-SYNTHETIC-0001",
  lifecycle_state: "NATIONAL_IDENTITY_PENDING_REVIEW",
  verification_state: "PENDING_REVIEW",
  can_access_medical_data: false,
  next_step: "await_in_person_review",
  requires_in_person_review: true,
  identity_submitted: true,
  health_identity_approved: false,
  official_verification: false,
  synthetic: true,
  notice: "synthetic_workflow_not_government_verification",
};
