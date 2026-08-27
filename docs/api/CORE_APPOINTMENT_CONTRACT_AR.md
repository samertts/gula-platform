# Core Appointment API Contract v1

## الغرض والنطاق

هذا العقد يحدد أول مسار canonical لطلب موعد وتأكيده في GULA. يعتمد القرار على session وworkspace وmembership وorganization وfacility وpermission التي يثبتها الخادم. لا يعتمد على role أو workspace يرسلهما frontend كحقيقة، ولا يفتح أي تكامل خارجي أو بيانات حقيقية.

## الموارد والحالات

| المورد | الحقول الأساسية | ملاحظة الحماية |
|---|---|---|
| `AppointmentSlot` | `id`, `workspace_id`, `provider_account_id`, `service_code`, `starts_at`, `ends_at`, `status`, `version` | يعاد من scope المصرح فقط؛ لا يظهر national/health ID |
| `Appointment` | `id`, `slot_id`, `patient_person_id`, `provider_account_id`, `organization_id`, `facility_id`, `workspace_id`, `purpose`, `state`, `version`, timestamps | `patient_person_id` opaque وقراءة المورد scoped |
| `IdempotencyReceipt` | actor/operation/key/fingerprint/response/status | داخلي ولا يعاد للعميل إلا عبر replay للـresponse |

الحالات المسموحة هي `REQUESTED`, `CONFIRMED`, `CHECKED_IN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW`, `RESCHEDULED`, `EXPIRED`. في هذه النسخة تنفذ الأوامر `REQUESTED → CONFIRMED` فقط، ويُرفض أي انتقال خارج `clinical_core.py`.

## Endpoints

### إنشاء فترة متاحة

`POST /api/v1/appointments/slots`

يتطلب `Authorization` عبر NIAM و`Idempotency-Key`. الجسم:

```json
{
  "workspace_id": "<opaque-id>",
  "provider_account_id": "<opaque-id>",
  "service_code": "GENERAL-CONSULT",
  "starts_at": "2030-01-01T10:00:00Z",
  "ends_at": "2030-01-01T10:30:00Z"
}
```

ينفذ الخادم permission `appointment.slot.manage` ويتحقق من provider داخل نفس organization/facility/workspace. يمنع unique provider window التكرار. يعيد `201` مع slot DTO.

### قراءة الفترات

`GET /api/v1/appointments/slots?workspace_id=<id>&starts_at=<datetime>&ends_at=<datetime>&limit=50&offset=0`

الاستجابة paginated ولا تعرض إلا الفترات `AVAILABLE` ضمن السياق الخادمي. الحد الأقصى لـ`limit` هو 100.

### طلب موعد

`POST /api/v1/appointments`

يتطلب `Authorization` و`Idempotency-Key`. الجسم:

```json
{
  "workspace_id": "<opaque-id>",
  "patient_person_id": "<opaque-id>",
  "slot_id": "<opaque-id>",
  "purpose": "TREATMENT"
}
```

للطلب الذاتي يجب أن يطابق patient الشخص المرتبط بهوية actor الفعالة. يتم تحميل slot داخل organization/facility/workspace مع lock قاعدة البيانات، ثم يتحقق provider والavailability، ثم ينشئ appointment ويحوّل slot إلى `BOOKED` في المعاملة نفسها. لا تعتمد العملية على availability في frontend.

### تأكيد موعد

`POST /api/v1/appointments/{appointment_id}/confirm?workspace_id=<id>`

يتطلب `Authorization`, `Idempotency-Key`, و`If-Match: "<version>"`. الجسم:

```json
{
  "reason": "Optional bounded operational reason"
}
```

يُسمح فقط للـpermission `appointment.confirm` ضمن scope، ويتحقق الخادم من version والحالة الحالية. النجاح يحول `REQUESTED` إلى `CONFIRMED` ويرفع version إلى 2. إعادة الطلب بنفس idempotency key وpayload تعيد نفس response؛ version قديم يعيد `VERSION_CONFLICT`.

### قراءة موعد وقائمته

`GET /api/v1/appointments/{appointment_id}?workspace_id=<id>` و`GET /api/v1/appointments?workspace_id=<id>&state=<state>&limit=50&offset=0`.

الاستعلامات تقيد organization/facility/workspace دائماً. إذا لم توجد `appointment.read`، يقتصر العرض على requester أو provider، ولا يحاول النظام إخفاء authorization خلف عدم إظهار الزر فقط.

## Error Contract

يستخدم الخادم payload المركزي التالي، مع إبقاء `detail` و`detail_ar` للتوافق مع العملاء القديمة:

```json
{
  "code": "VERSION_CONFLICT",
  "message": "The appointment changed before this operation.",
  "details": {
    "correlation_id": "<request-correlation-id>",
    "message_ar": "تغير الموعد قبل تنفيذ العملية."
  },
  "request_id": "<request-id>",
  "timestamp": "<utc-iso8601>",
  "detail": "The appointment changed before this operation.",
  "detail_ar": "يوجد تعارض يمنع إكمال العملية."
}
```

عند غياب `If-Match` يعيد الخادم HTTP `428` مع `PRECONDITION_REQUIRED`؛ وعند إرسال version قديم يعيد HTTP `409` مع `VERSION_CONFLICT`. القيم المستقرة الأخرى في هذا العقد هي `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `IDEMPOTENCY_CONFLICT`, `SLOT_UNAVAILABLE`, `RATE_LIMITED`, و`INTERNAL_ERROR`. لا يعاد stack trace أو سبب عضوية دقيق للعميل.

## الأمن والتدقيق

كل write يمر عبر session/account/identity/workspace/membership/role/permission وobject/tenant checks. تُسجل أحداث النجاح والرفض في `CanonicalAuditService` مع actor وscope وtarget وaction وdecision وcorrelation/request IDs وbefore/after عند الانتقال. لا توجد delete route للأحداث، ولا تُسجل tokens أو كلمات المرور أو national/health IDs أو تفاصيل صحية غير لازمة.

## سياسة Demo وLive

يبقى Demo synthetic/read-only/isolated. Live يقرأ ويكتب من canonical backend فقط بعد تفعيل صريح واختبارات frontend contract. لا يُستخدم legacy booking API أو broad API أو direct database access أو fake successful write. لا يُفتح write allowlist في `frontend-v3` كجزء من هذه الموجة.

## التوافق والتراجع

تبقى National Scheduling tables وroutes القديمة دون حذف. migration الجديدة additive. يتم الانتقال المستقبلي عبر `add → backfill → validate → shadow-read → switch → deprecate → remove` مع rollback plan منفصل. لا توجد migration تلقائية إلى الإنتاج من هذا العقد.
