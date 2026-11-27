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

export type CitizenRegistrationLocale = "ar" | "en";

interface CitizenStatusLabels {
  title: string;
  description: string;
  regionLabel: string;
  unknownState: string;
  verificationPrefix: string;
  officialVerificationUnavailable: string;
  inPersonReview: string;
  medicalEnabled: string;
  medicalDenied: string;
  medicalDescription: string;
  caseReference: string;
  syntheticNotice: string;
  lifecycle: Record<string, string>;
  nextStep: Record<string, string>;
}

const AR_LABELS: CitizenStatusLabels = {
  title: "حالة طلب إنشاء الحساب",
  description: "عرض آمن لحالة الطلب داخل البيئة التجريبية",
  regionLabel: "حالة طلب إنشاء الحساب",
  unknownState: "حالة غير معروفة",
  verificationPrefix: "حالة التحقق",
  officialVerificationUnavailable: "التحقق الحكومي الرسمي: غير متاح",
  inPersonReview: "مراجعة حضورية مطلوبة",
  medicalEnabled: "الوصول للبيانات الطبية: مفعّل",
  medicalDenied: "الوصول للبيانات الطبية: غير مفعّل",
  medicalDescription: "لا تُمنح الصلاحية قبل استكمال التحقق واعتماد الجهة المخولة.",
  caseReference: "رقم الحالة التجريبي",
  syntheticNotice:
    "بيانات تجريبية داخل بيئة معزولة. هذه الحالة ليست تحققاً حكومياً ولا تمنح الوصول إلى البيانات الطبية.",
  lifecycle: {
    NO_ACCOUNT: "لا يوجد حساب",
    INITIAL_ACCOUNT_CREATED: "تم إنشاء الحساب الأولي",
    CONTACT_VERIFIED: "تم التحقق من وسيلة التواصل",
    NATIONAL_IDENTITY_SUBMITTED: "تم تقديم بيانات الهوية الوطنية",
    NATIONAL_IDENTITY_PENDING_REVIEW: "قيد المراجعة الحضورية",
    HEALTH_IDENTITY_APPROVED: "تمت الموافقة على الهوية الصحية",
    SERVICE_ACTIVE: "الخدمة فعّالة",
    REJECTED: "مرفوض",
    SUSPENDED: "موقوف",
    RESUBMITTED: "تم إعادة تقديم الطلب",
    APPEAL_RECONSIDERED: "قيد إعادة النظر",
    MANUAL_REVIEW_REQUESTED: "أُحيل الطلب للمراجعة اليدوية",
  },
  nextStep: {
    verify_contact: "الخطوة التالية: التحقق من رقم الهاتف أو وسيلة التواصل.",
    submit_identity: "الخطوة التالية: تقديم بيانات الوثيقة الأصلية للمراجعة.",
    await_in_person_review: "الخطوة التالية: انتظار مراجعة مختصة في موقع معتمد.",
    activation_pending_owner_approval: "الخطوة التالية: تفعيل الخدمة بعد اعتماد الجهة المخولة.",
    none: "لا توجد خطوة مطلوبة حالياً.",
    contact_support: "الخطوة التالية: التواصل مع الدعم.",
  },
};

// English fallback is used when a translation is incomplete or the caller
// selects the English locale. Unknown keys are shown verbatim, never invented.
const EN_LABELS: CitizenStatusLabels = {
  title: "Account registration status",
  description: "Safe view of a synthetic registration case",
  regionLabel: "Account registration status",
  unknownState: "Unknown state",
  verificationPrefix: "Verification state",
  officialVerificationUnavailable: "Official government verification: unavailable",
  inPersonReview: "In-person review required",
  medicalEnabled: "Medical data access: enabled",
  medicalDenied: "Medical data access: disabled",
  medicalDescription: "Access is not granted before verification and authorized approval.",
  caseReference: "Synthetic case reference",
  syntheticNotice:
    "Synthetic data in an isolated environment. This status is not government verification and does not grant medical data access.",
  lifecycle: {
    NO_ACCOUNT: "No account",
    INITIAL_ACCOUNT_CREATED: "Initial account created",
    CONTACT_VERIFIED: "Contact verified",
    NATIONAL_IDENTITY_SUBMITTED: "Identity evidence submitted",
    NATIONAL_IDENTITY_PENDING_REVIEW: "Pending in-person review",
    HEALTH_IDENTITY_APPROVED: "Health identity approved",
    SERVICE_ACTIVE: "Service active",
    REJECTED: "Rejected",
    SUSPENDED: "Suspended",
    RESUBMITTED: "Resubmitted",
    APPEAL_RECONSIDERED: "Appeal under reconsideration",
    MANUAL_REVIEW_REQUESTED: "Manual review requested",
  },
  nextStep: {
    verify_contact: "Next step: verify a phone number or contact channel.",
    submit_identity: "Next step: present original document evidence for review.",
    await_in_person_review: "Next step: wait for an authorized in-person review.",
    activation_pending_owner_approval: "Next step: activation awaits authorized approval.",
    none: "No action is currently required.",
    contact_support: "Next step: contact support.",
  },
};

function resolveLabels(locale: CitizenRegistrationLocale): CitizenStatusLabels {
  return locale === "en" ? EN_LABELS : AR_LABELS;
}

// Only bounded, non-assertive tokens may be shown as an official state.
// "VERIFIED" and unknown tokens are never rendered as verification claims,
// even if a future caller sets official_verification to true.
const SAFE_OFFICIAL_VERIFICATION_STATES = new Set([
  "UNVERIFIED",
  "NOT_VERIFIED",
  "PENDING_REVIEW",
  "REVIEW_REQUIRED",
]);

export function CitizenRegistrationStatus({
  status,
  locale = "ar",
}: {
  status: RegistrationStatusPayload;
  locale?: CitizenRegistrationLocale;
}) {
  const labels = resolveLabels(locale);
  const lifecycleLabel = labels.lifecycle[status.lifecycle_state] ?? status.lifecycle_state;
  const nextStep = labels.nextStep[status.next_step] ?? labels.nextStep.contact_support;
  const medicalLabel = status.can_access_medical_data ? labels.medicalEnabled : labels.medicalDenied;
  const showVerificationState =
    status.official_verification && SAFE_OFFICIAL_VERIFICATION_STATES.has(status.verification_state);

  return (
    <section
      dir={locale === "ar" ? "rtl" : "ltr"}
      lang={locale}
      aria-label={labels.regionLabel}
    >
      <Card>
        <CardHeader>
          <CardTitle>{labels.title}</CardTitle>
          <CardDescription>{labels.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{lifecycleLabel}</Badge>
            {showVerificationState ? (
              <Badge variant="secondary">
                {labels.verificationPrefix}: {status.verification_state}
              </Badge>
            ) : (
              <Badge variant="secondary">{labels.officialVerificationUnavailable}</Badge>
            )}
            {status.requires_in_person_review && (
              <Badge variant="warning">{labels.inPersonReview}</Badge>
            )}
          </div>
          <AdaptiveStatus
            state={status.can_access_medical_data ? "enabled" : "permission_denied"}
            label={medicalLabel}
            description={labels.medicalDescription}
          />
          <p role="status" aria-live="polite" className="text-sm font-semibold">
            {nextStep}
          </p>
          <p className="text-xs leading-5 text-muted-foreground">{labels.syntheticNotice}</p>
          <p className="text-xs text-muted-foreground" aria-label={labels.caseReference}>
            {labels.caseReference}: {status.case_reference}
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
