# P0-1 — عقد القراءة السريرية الموحد

**الحالة:** CONTRACT_BASELINE — لا توجد routes مفعلة بهذا العقد في هذه المرحلة.
**النطاق:** `patients.read` و`orders.read` فقط.
**مصدر السجل:** GULA clinical system of record.
**التاريخ:** 2026-08-14.

## قرار namespace

يعتمد PR-1 namespace جديدًا versioned هو `/api/v1/clinical`، ويُسجل router في `backend/app/factory.py` إلى جانب routers المنصة الحالية. هذا لا يعيد استخدام `/patients` أو `/orders` legacy، ولا يحذفها. إذا كشف PR-1 أثناء mount review وجود namespace versioned مؤسسي ملزم، يجب تحديث هذا القرار قبل merge لا إنشاء route مكرر.

العقدان المقترحان هما:

```text
GET /api/v1/clinical/patients
GET /api/v1/clinical/orders
```

ولا يتضمن هذا الإصدار أي write operation أو sample/result operation أو validation/release أو financial operation.

## مصدر الأدلة وحدود delegation

تستخدم واجهتا `frontend-v3/src/pages/patients/PatientsPage.tsx` و`frontend-v3/src/pages/orders/OrdersPage.tsx` عقدي `patients.read` و`orders.read` وتعلنان workspace context مطلوبًا. أما backend الحالي فيوفر خدمات legacy في `app/services/patient_service.py` و`app/services/order_service.py` تعتمد على `lab_id`. سيستخدم PR-1 هذه الخدمات كحد delegation فقط بعد إثبات السياق canonical، مع mapping استجابة typed وإزالة الحقول الحساسة؛ ولن تصبح `LabUser` أو `lab_id` سلطة تفويض.

يوجد بالفعل `ClinicalAuthorizationContextService` و`ClinicalScopeBridgeService` و`LegacyAccountLink`. ستُستخدم هذه primitives داخل adapter بعد نجاح `NiamActor` وworkspace/facility authorization. لا يُنشأ mapping ثانٍ ولا يتم دمج هويات غير مؤكدة.

## Request schema

يقبل كل endpoint query parameters التالية فقط:

| الحقل | النوع | الافتراضي/الحد | القاعدة |
|---|---|---|---|
| `cursor` | string اختياري | حد أقصى 200 | opaque server-issued cursor فقط؛ لا يقبل IDs سياقية |
| `limit` | integer | 50، من 1 إلى 100 | لا يوجد unlimited enumeration |
| `search` | string اختياري | من حرفين إلى 80 | بحث display-name محدود؛ تُرفض قيم phone/national/order identifier enumeration |

الـgateway لا يقبل `organization_id` أو `facility_id` أو `workspace_id` أو `lab_id` أو `actor_id` من query/body كـauthoritative context. تُشتق هذه القيم من الجلسة وworkspace context الخادمي.

يُمنع إرسال query fields إضافية، وتُرجع validation errors بصيغة `422` دون تنفيذ أي clinical query.

## Response envelope

كل endpoint يعيد envelope typed بالشكل المنطقي التالي:

```json
{
  "contract_version": "1.0",
  "request_id": "server-generated-uuid",
  "correlation_id": "server-or-propagated-uuid",
  "workspace_context": {
    "organization_id": "opaque-id",
    "facility_id": "opaque-id",
    "workspace_id": "opaque-id",
    "department_id": null
  },
  "items": [],
  "limit": 50,
  "next_cursor": null,
  "total": null
}
```

لا تُعاد ORM objects مباشرة، ولا تُعاد policy internals أو raw SQL details. `request_id` server-controlled، و`correlation_id` يُحافظ عليه إن كان موجودًا ضمن request boundary وإلا يُنشأ خادميًا.

### PatientRead

| الحقل | النوع | الملاحظة |
|---|---|---|
| `id` | string | opaque resource identifier |
| `display_name` | string | الاسم المطلوب للجدول فقط |
| `birth_date` | string/null | يعاد فقط إن كان ضمن عقد العرض المعتمد |
| `gender` | string/null | قيمة محدودة |
| `created_at` | datetime/null | metadata تشغيلية |

لا يعاد `national_id` أو `national_id_hash` أو `family_id_hash` أو الهاتف أو العنوان أو `lab_id` أو biometric/identity document fields.

### OrderRead

| الحقل | النوع | الملاحظة |
|---|---|---|
| `id` | string | opaque resource identifier |
| `patient_display_name` | string/null | لا يعاد patient phone أو national identifier |
| `practitioner_display_name` | string/null | display field فقط |
| `status` | string | حالة الطلب دون result payload |
| `test_count` | integer | count فقط؛ لا results أو samples |
| `created_at` | datetime/null | metadata تشغيلية |

لا يعاد `results` أو `samples` أو share links أو patient phone أو validation metadata غير اللازمة للواجهة الأولى.

## Authentication and authorization

كل طلب يمر أولًا عبر `get_current_niam_actor`، ثم resolver يثبت account/session وactive workspace وorganization وfacility وmembership. بعد ذلك يستدعى `AuthorizationDecisionService` من داخل gateway بسياق server-derived يتضمن:

| المورد | الفعل | permission |
|---|---|---|
| `clinical_patient` | `read` | `patients.read` |
| `clinical_order` | `read` | `orders.read` |

لا تُستنتج الصلاحية من frontend role names، ولا تكفي permission وحدها دون organization/facility/workspace/resource scope.

## Error model

| HTTP | code | المعنى |
|---:|---|---|
| 401 | `UNAUTHENTICATED` | session missing/expired/revoked/invalid |
| 403 | `UNAUTHORIZED` | membership/permission/scope/policy denied |
| 404 | `NOT_FOUND` | المورد غير موجود ضمن النطاق؛ دون كشف وجوده خارج النطاق |
| 409 | `CONTEXT_CONFLICT` | workspace context تغير أو لم يعد صالحًا أثناء الطلب |
| 422 | `INVALID_REQUEST` | query schema أو search restriction غير صالح |
| 429 | `RATE_LIMITED` | تجاوز حد القراءة |
| 500/503 | `UNAVAILABLE` | failure داخلي؛ لا fallback إلى legacy authorization |

كل error يحتوي `code`, `message` آمنة، `request_id` و`correlation_id`. لا تُعرض أسباب داخلية مثل policy IDs أو SQL أو identity mapping details.

## Resource scope

قبل query يجب إثبات:

1. active account وvalid session.
2. active membership للـorganization.
3. workspace active وينتمي إلى organization.
4. facility active وتنتمي إلى organization.
5. membership/role يسمحان بالـworkspace/facility.
6. `AuthorizationDecisionService` يسمح بالـresource/action/permission.
7. resource query يحتوي mandatory organization/facility/workspace predicates.
8. legacy adapter، إن لزم، يُشتق من canonical context ولا يقبل `lab_id` من العميل.

أي فشل يؤدي إلى `BLOCKED_SAFE`، ولا ينفذ unscoped clinical query.

## Audit

يسجل gateway قرارات allow/deny الحساسة عبر canonical audit chain، متضمنة actor، action، resource class، organization، facility، workspace، decision، reason code، request ID، correlation ID، timestamp. لا تُسجل كلمات البحث الخام الحساسة أو passwords أو tokens أو OTP أو secrets أو identifiers غير اللازمة.

أمثلة deny reason codes: `missing_workspace`, `workspace_inactive`, `membership_missing`, `facility_mismatch`, `permission_denied`, `cross_tenant_scope`, `invalid_context`, `expired_session`.

## Compatibility and activation

تبقى `DIRECT_REST_SCOPED_READS_BLOCKED = true` حتى ينجح PR-1/PR-2 واختبارات PostgreSQL. لا يقرأ frontend-v3 من `/patients` أو `/orders` legacy، ولا يستخدم frontend-v2 أو mock/synthetic fallback. feature flag الخادمي يبدأ `OFF`، ويُفتح لاحقًا فقط إلى `INTERNAL` ثم `PILOT` بعد security review وموافقة بشرية.

## Acceptance for PR-0

يُقبل هذا العقد فقط إذا نجحت schema tests، وثبتت الحقول الحساسة المستبعدة، وثبتت حدود page/search، ووثقت routes/errors/auth/scope/audit. لا يُعتبر PR-0 تفعيلًا للقراءة السريرية ولا يغلق P0 وحده.
