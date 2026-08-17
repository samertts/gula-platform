# مواصفة API لطابور المزامنة ومعالجة تعارض النسخ في GULA

**الإصدار المقترح:** Sync API v1
**النطاق:** العمل دون اتصال، مزامنة سجلات الطوارئ، Patient Flow، المواعيد، والأحداث السريرية القابلة للمراجعة
**الحالة:** تصميم تنفيذي؛ لا يعني أن Offline Sync أصبح منفذًا في الفرع الحالي

## 1. الهدف ونطاق التصميم

يضيف هذا التصميم طبقة مزامنة مستقلة تستقبل أوامر الأجهزة التي عملت دون اتصال، وتتحقق منها، ثم تطبقها عبر الخدمات السريرية الحالية. لا تكتب طبقة المزامنة مباشرة إلى جداول `Encounter` أو `Appointment`؛ بل تستدعي الخدمات التي تطبق الصلاحيات، آلة الحالات، عزل المؤسسة، النسخ، والتدقيق.

المبدأ الحاكم هو:

> لا توجد عملية سريرية «مقبولة» لمجرد وصولها إلى طابور المزامنة. القبول لا يحدث إلا بعد التحقق من الجهاز والمستخدم والمؤسسة والصلاحية والنسخة وصحة الانتقال.

وتنفصل ثلاث حالات يجب ألا تختلط:

| المجال | أمثلة |
|---|---|
| الحالة السريرية | `arrived`, `triaged`, `in_progress`, `admitted`, `discharged` |
| حالة المزامنة | `captured_local`, `queued`, `processing`, `accepted`, `duplicate`, `conflict`, `rejected`, `dead_letter` |
| حالة المراجعة | `not_required`, `pending`, `in_review`, `resolved`, `rejected` |

## 2. قواعد غير قابلة للتجاوز

| القاعدة | التنفيذ الإلزامي |
|---|---|
| منع التكرار | كل عملية تحمل `operation_id` و`idempotency_key` فريدًا ضمن المؤسسة والجهاز أو نطاق العملية. |
| منع الكتابة فوق نسخة أحدث | كل تعديل يحمل `base_version`، ويُرفض إذا لم تطابق النسخة الخادمية الحالية. |
| عدم تجاوز آلة الحالات | تُطبق انتقالات Patient Flow عبر `transition_flow_state` أو خدمة معتمدة مكافئة، وليس بتحديث عمود الحالة مباشرة. |
| عدم حل التعارض بصمت | أي تعارض سريري ينشئ سجل تعارض وسجل تدقيق، ولا يستخدم `last-write-wins`. |
| عزل المؤسسة | يُستخرج `lab_id` من جلسة المستخدم أو هوية الجهاز الموثوقة، ولا يُقبل من جسم الطلب كمصدر ثقة. |
| أولوية الطوارئ | عمليات الوصول والفرز الحرجة لها أولوية أعلى من العمليات الإدارية، دون تجاوز التحقق. |
| تدقيق كامل | كل قبول أو رفض أو تعارض أو حل تعارض ينتج حدث تدقيق append-only. |
| إعادة المحاولة الآمنة | إعادة المحاولة لا تعيد الأثر الجانبي؛ تستخدم مفتاح العملية ونتيجتها السابقة. |

## 3. نموذج عملية المزامنة

```json
{
  "operation_id": "op_01J...",
  "idempotency_key": "idem_01J...",
  "device_id": "ER-TABLET-02",
  "client_sequence": 1842,
  "operation_type": "encounter.transition",
  "priority": "critical",
  "entity": {
    "type": "Encounter",
    "local_id": "OFF-2026-000184",
    "server_id": "enc_01J..."
  },
  "base_version": 7,
  "captured_at": "2026-08-17T14:21:11Z",
  "payload": {
    "target_state": "triaged",
    "triage_priority": "stat"
  },
  "integrity": {
    "payload_hash": "sha256:...",
    "signature": "base64url..."
  }
}
```

يُمنع وضع بيانات صحية كاملة داخل `idempotency_key` أو رؤوس HTTP. المفتاح معرّف عشوائي لا يحمل رقم المريض أو التشخيص.

## 4. حالات العملية

```text
captured_local
      ↓
queued
      ↓
processing
   ↙    ↓      ↘
accepted duplicate conflict
                    ↓
                 in_review
              ↙             ↘
          resolved        rejected

processing → rejected
processing → dead_letter  (بعد فشل متكرر مصحوب بتدقيق)
```

| الحالة | المعنى |
|---|---|
| `captured_local` | سجّلها الجهاز محليًا ولم تُرسل بعد. |
| `queued` | وصلت إلى API أو أُدرجت في طابور داخلي. |
| `processing` | يجري التحقق والتطبيق. |
| `accepted` | طبقت العملية على مصدر الحقيقة وأعيدت النتيجة. |
| `duplicate` | العملية مكررة وأعيدت نتيجة العملية الأصلية. |
| `conflict` | النسخة أو الحالة أو الهوية تتعارض مع الخادم. |
| `rejected` | فشل تحقق أو صلاحية أو مخطط أو مؤسسة. |
| `dead_letter` | فشل متكرر يحتاج تدخلًا تشغيليًا، مع بقاء البيانات محفوظة. |

## 5. مسارات API الأساسية

### 5.1 تسجيل الجهاز أو تجديد قدرته على المزامنة

```http
POST /api/v1/sync/devices/{device_id}/session
Cookie: access_token=...
X-Device-ID: ER-TABLET-02
X-App-Version: 3.2.0
```

يستخدم هذا المسار عند اتصال الجهاز لأول مرة أو بعد انتهاء جلسة مزامنة. لا يسمح بتسجيل جهاز جديد أو تغيير المؤسسة من وضع Offline. التسجيل الأول يحتاج اتصالًا وهوية موظف موثقة.

الاستجابة:

```json
{
  "device_id": "ER-TABLET-02",
  "lab_id": 12,
  "hospital_id": 7,
  "sync_session_id": "ss_01J...",
  "expires_at": "2026-08-17T22:00:00Z",
  "allowed_operation_types": [
    "encounter.arrival",
    "encounter.triage",
    "encounter.vital_sign",
    "encounter.note",
    "encounter.transition"
  ],
  "max_batch_size": 100,
  "policy_version": "offline-emergency-1"
}
```

### 5.2 فحص حالة المزامنة

```http
GET /api/v1/sync/status?device_id=ER-TABLET-02
Cookie: access_token=...
X-Device-ID: ER-TABLET-02
```

الاستجابة:

```json
{
  "device_id": "ER-TABLET-02",
  "server_time": "2026-08-17T14:32:00Z",
  "accepted_through_sequence": 1810,
  "queued_count": 19,
  "processing_count": 2,
  "conflict_count": 1,
  "oldest_pending_at": "2026-08-17T14:21:11Z",
  "mode": "degraded_allowed",
  "retry_after_seconds": 5
}
```

لا يُستخدم هذا المسار لقراءة بيانات سريرية واسعة؛ هو مسار حالة تشغيلي محدود.

### 5.3 استقبال دفعة مزامنة

```http
POST /api/v1/sync/operations:batch
Cookie: access_token=...
X-Device-ID: ER-TABLET-02
X-GULA-Operation-ID: batch_01J...
X-GULA-Request-Fingerprint: sha256:...
Content-Type: application/json
```

جسم الطلب:

```json
{
  "sync_session_id": "ss_01J...",
  "client_id": "ER-TABLET-02",
  "client_sequence_from": 1811,
  "client_sequence_to": 1829,
  "operations": [
    {
      "operation_id": "op_01J...",
      "idempotency_key": "idem_01J...",
      "client_sequence": 1811,
      "operation_type": "encounter.arrival",
      "priority": "critical",
      "entity_type": "Encounter",
      "entity_local_id": "OFF-2026-000184",
      "entity_server_id": null,
      "base_version": null,
      "captured_at": "2026-08-17T14:21:11Z",
      "payload": {
        "patient_id": "np_01J...",
        "hospital_id": 7,
        "encounter_type": "outpatient",
        "priority": "stat",
        "is_emergency": true
      },
      "payload_hash": "sha256:...",
      "signature": "base64url..."
    }
  ]
}
```

الاستجابة تستخدم نتيجة مستقلة لكل عملية حتى لا يؤدي فشل عملية واحدة إلى إخفاء نتيجة بقية الدفعة:

```json
{
  "batch_id": "batch_01J...",
  "accepted_count": 1,
  "duplicate_count": 0,
  "conflict_count": 1,
  "rejected_count": 0,
  "results": [
    {
      "operation_id": "op_01J...",
      "status": "accepted",
      "server_id": "enc_01J...",
      "server_version": 1,
      "accepted_at": "2026-08-17T14:32:02Z"
    },
    {
      "operation_id": "op_01J...",
      "status": "conflict",
      "conflict_id": "conf_01J...",
      "server_id": "enc_01J...",
      "server_version": 8,
      "reason_code": "STALE_VERSION",
      "next_action": "review_required"
    }
  ]
}
```

الدفعة لا تُعالج كمعاملة واحدة إذا كانت العمليات مستقلة؛ كل عملية تحتاج معاملة ACID مستقلة أو مجموعة مترابطة معرفة صراحة. أما العمليات التي يجب أن تنجح أو تفشل معًا فيجب إرسالها كـ`operation_group_id`، مع حد أقصى صغير ومعلن.

### 5.4 جلب تغييرات الخادم للجهاز

```http
GET /api/v1/sync/changes?cursor=cur_01J...&limit=100
Cookie: access_token=...
X-Device-ID: ER-TABLET-02
```

الاستجابة:

```json
{
  "cursor": "cur_01J_next",
  "has_more": true,
  "changes": [
    {
      "change_id": "chg_01J...",
      "entity_type": "Encounter",
      "entity_id": "enc_01J...",
      "version": 8,
      "change_type": "updated",
      "changed_fields": ["flow_state", "priority"],
      "changed_at": "2026-08-17T14:31:59Z",
      "data": {
        "flow_state": "triaged",
        "priority": "stat"
      }
    }
  ]
}
```

يجب أن تكون التغييرات محدودة بنطاق المؤسسة والجهاز والدور، ولا يجوز أن يتحول endpoint التغييرات إلى تصدير كامل للسجل الطبي.

### 5.5 إعادة محاولة عملية معلقة

```http
POST /api/v1/sync/operations/{operation_id}:retry
Cookie: access_token=...
X-Device-ID: ER-TABLET-02
```

لا يعيد المسار إنشاء عملية جديدة؛ يعيد تشغيل العملية الأصلية بنفس `operation_id` و`idempotency_key` بعد التحقق من عدم قبولها سابقًا.

### 5.6 قراءة تعارضات الجهاز أو المؤسسة

```http
GET /api/v1/sync/conflicts?status=pending&hospital_id=7&limit=50
Cookie: access_token=...
```

الصلاحيات المقترحة:

| العملية | الصلاحية |
|---|---|
| قراءة تعارضات المؤسسة | `sync:conflict:read` |
| عرض القيم قبل وبعد | `sync:conflict:inspect` |
| حل تعارض سريري | `sync:conflict:resolve:clinical` |
| حل تعارض إداري | `sync:conflict:resolve:administrative` |
| إعادة فتح قرار | `sync:conflict:reopen` |

### 5.7 عرض تعارض محدد

```http
GET /api/v1/sync/conflicts/{conflict_id}
Cookie: access_token=...
```

الاستجابة:

```json
{
  "conflict_id": "conf_01J...",
  "status": "pending",
  "conflict_type": "clinical_version",
  "entity_type": "Encounter",
  "entity_id": "enc_01J...",
  "hospital_id": 7,
  "operation": {
    "operation_id": "op_01J...",
    "device_id": "ER-TABLET-02",
    "user_id": "usr_01J...",
    "captured_at": "2026-08-17T14:21:11Z",
    "base_version": 7
  },
  "server_snapshot": {
    "version": 8,
    "flow_state": "triaged",
    "priority": "urgent",
    "changed_at": "2026-08-17T14:29:04Z",
    "changed_by": "usr_01J_other"
  },
  "local_proposal": {
    "target_state": "in_progress",
    "priority": "stat"
  },
  "allowed_resolutions": [
    "accept_server",
    "accept_local_proposal",
    "apply_non_conflicting_fields",
    "reject_operation"
  ]
}
```

لا تعرض الواجهة بيانات أكثر مما يحتاجه المراجع، وتخفي الحقول الحساسة غير اللازمة للمقارنة.

### 5.8 حل التعارض

```http
POST /api/v1/sync/conflicts/{conflict_id}:resolve
Cookie: access_token=...
If-Match: "conflict-version-3"
Content-Type: application/json
```

جسم الطلب:

```json
{
  "resolution": "accept_local_proposal",
  "reason_code": "CLINICAL_REASSESSMENT",
  "reason_note": "أعيد تقييم الحالة بواسطة الطبيب المناوب بعد وصول المريض.",
  "expected_entity_version": 8,
  "apply_fields": ["priority", "flow_state"]
}
```

الاستجابة:

```json
{
  "conflict_id": "conf_01J...",
  "status": "resolved",
  "resolution": "accept_local_proposal",
  "entity_id": "enc_01J...",
  "new_entity_version": 9,
  "resolved_by": "usr_01J_reviewer",
  "resolved_at": "2026-08-17T14:35:10Z",
  "audit_event_id": "audit_01J..."
}
```

إذا تغير السجل بين عرض التعارض وحله، يعيد الخادم `412 Precondition Failed` ويُنشئ قراءة جديدة مطلوبة بدل تطبيق قرار قديم.

### 5.9 الإقرار بالمزامنة

```http
POST /api/v1/sync/acknowledgements
Cookie: access_token=...
X-Device-ID: ER-TABLET-02
```

جسم الطلب:

```json
{
  "sync_session_id": "ss_01J...",
  "acknowledgements": [
    {
      "operation_id": "op_01J...",
      "client_sequence": 1811,
      "device_applied_status": "accepted_by_server"
    }
  ]
}
```

الإقرار لا يغير الحالة السريرية ولا يعتمد العملية؛ وظيفته إعلام الخادم بأن الجهاز استلم النتيجة ويمكنه إزالة النسخة المحلية وفق سياسة الاحتفاظ.

## 6. أكواد HTTP والأخطاء

| الكود | الاستخدام |
|---:|---|
| `200` | استجابة حالة أو دفعة تحتوي نتائج فردية. |
| `201` | إنشاء مورد مزامنة أو تعارض جديد عند الحاجة. |
| `202` | قبول العملية للطابور دون تطبيق فوري، مع `operation_id`. |
| `400` | مخطط طلب غير صحيح أو حقل ناقص. |
| `401` | جلسة غير صالحة أو منتهية. |
| `403` | المستخدم أو الجهاز لا يملك الصلاحية أو النطاق. |
| `404` | المؤسسة أو السجل أو التعارض غير موجود ضمن نطاق المستخدم. |
| `409` | تكرار غير متطابق أو تعارض أعمال لا يمكن تطبيقه. |
| `412` | فشل شرط `If-Match` أو نسخة الكيان تغيرت. |
| `422` | انتقال سريري غير مسموح أو بيانات لا تتفق مع قواعد المجال. |
| `428` | العملية الحساسة لا تحتوي `base_version` أو `If-Match`. |
| `429` | تجاوز حد الطلب؛ يعاد بعد `Retry-After`. |
| `503` | الخدمة غير متاحة؛ تبقى العملية محليًا أو في الطابور ولا تُعتبر مقبولة. |

صيغة الخطأ الموحدة:

```json
{
  "error": {
    "code": "STALE_VERSION",
    "message": "The entity changed after the operation was captured.",
    "message_ar": "تغير السجل بعد التقاط العملية؛ يلزم إجراء مراجعة.",
    "operation_id": "op_01J...",
    "conflict_id": "conf_01J...",
    "current_version": 8,
    "retryable": false,
    "audit_event_id": "audit_01J..."
  }
}
```

## 7. سياسة الحل الآلي

| نوع العملية | الحل الآلي |
|---|---|
| إعادة إرسال عملية لها نفس المفتاح ونفس البصمة | إعادة نتيجة العملية الأولى. |
| إضافة حدث سريري جديد مستقل | قبولها كحدث append-only إذا كانت الهوية والصلاحية صحيحتين. |
| تحديث حقل إداري غير حساس | يمكن تطبيقه بعد فحص النسخة وتسجيل التدقيق. |
| تغيير الأولوية أو الحالة | رفض التعارض وإحالته لمراجع مخول. |
| قبول أو خروج أو نقل | لا حل تلقائي عند تعارض النسخة أو المؤسسة. |
| ربط هوية مؤقتة بهوية وطنية | مراجعة هوية إلزامية. |
| نتيجة مخبرية أو اعتماد طبي | لا يسمح Offline بالاعتماد النهائي؛ يحتاج خدمة ومستخدمًا مخولًا واتصالًا. |

لا يطبق النظام قاعدة `last-write-wins` على البيانات السريرية. وإذا استخدم دمج الحقول غير المتعارضة، يجب أن يكون الدمج محددًا في سياسة لكل نوع مورد، لا قرارًا عامًا داخل محرك المزامنة.

## 8. الأولوية والضغط

يجب أن يحتوي كل أمر على `priority`، لكن الأولوية لا تمنح صلاحية ولا تتجاوز التحقق. الترتيب المقترح للطابور:

```text
critical clinical
urgent clinical
routine clinical
administrative
telemetry / diagnostics
```

عند امتلاء الطابور، تُحجز سعة للعمليات الحرجة، ويُؤجل غير السريري. يجب تطبيق backpressure بدل قبول عمليات بلا قدرة على تخزينها. ويعيد API `429` أو `503` مع `Retry-After` عندما يتعذر ضمان المعالجة.

## 9. الأمن وسجل التدقيق

تستخدم الطلبات جلسة مصادقة عبر Cookie آمنة `HttpOnly` مع حماية CSRF، وربطًا بـ`X-Device-ID`، والتحقق من أن الجهاز مسجل داخل المؤسسة. لا يثق الخادم بـ`lab_id` أو `hospital_id` المرسل من العميل؛ يستخرج النطاق من هوية الجلسة وسياسة الجهاز ثم يقارن قيمة الطلب به.

كل عملية قبول أو رفض أو تعارض أو حل تعارض تسجل:

```text
audit_event_id
user_id
device_id
lab_id
hospital_id
action
entity_type
entity_id
operation_id
before_version
after_version
before_state
proposed_state
result
reason_code
timestamp_utc
request_id
```

يجب أن يكون سجل التدقيق append-only، وأن تكون قراءة السجل محدودة بدور مناسب، وألا تُسجل الأسرار أو رموز الجلسة داخل payload التدقيق.

## 10. تصميم الجداول المقترح

### `sync_operations`

| الحقل | الغرض |
|---|---|
| `id` | معرف العملية الداخلي. |
| `operation_id` | معرف العميل الفريد. |
| `idempotency_key` | منع التكرار ضمن النطاق. |
| `device_id` | مصدر العملية. |
| `user_id` | الممارس الذي التقطها. |
| `lab_id`, `hospital_id` | النطاق المؤسسي. |
| `operation_type` | نوع الأمر المسموح. |
| `entity_type`, `entity_id` | مصدر الحقيقة المتأثر. |
| `base_version` | النسخة عند الالتقاط. |
| `payload_hash` | سلامة الحمولة. |
| `payload_encrypted` | الحمولة المشفرة وفق سياسة الاحتفاظ. |
| `priority` | أولوية المعالجة. |
| `status` | حالة المزامنة. |
| `attempt_count` | عدد المحاولات. |
| `next_attempt_at` | وقت إعادة المحاولة. |
| `accepted_at` | وقت القبول الخادمي. |
| `created_at`, `updated_at` | التدقيق التشغيلي. |

### `sync_conflicts`

| الحقل | الغرض |
|---|---|
| `id` | معرف التعارض. |
| `operation_id` | العملية المسببة. |
| `entity_id` | الكيان المتعارض. |
| `conflict_type` | نسخة، حالة، هوية، نطاق، أو صلاحية. |
| `server_version` | النسخة عند اكتشاف التعارض. |
| `local_proposal` | الاقتراح المحلي المشفر. |
| `server_snapshot` | لقطة الخادم اللازمة للمراجعة. |
| `status` | pending، in_review، resolved، rejected. |
| `resolved_by`, `resolved_at` | هوية ووقت الحل. |
| `resolution_reason` | سبب القرار الإلزامي. |
| `resolution_version` | حماية قرار الحل من التعارض الثاني. |

يجب إضافة فهرس فريد على `(lab_id, device_id, idempotency_key)`، مع فهارس على `status`, `priority`, `next_attempt_at`, و`entity_id`. كما يجب تطبيق سياسة احتفاظ وحذف آمن للحمولات المحلية والنسخ القديمة.

## 11. تسلسل نموذجي لعملية حرجة

```text
الجهاز                     API المزامنة             Encounter Service       التدقيق
  |                             |                          |                  |
  | POST batch                  |                          |                  |
  |---------------------------->|                          |                  |
  |                             | تحقق الجهاز/الصلاحية    |                  |
  |                             | تحقق idempotency        |                  |
  |                             | تحقق base_version       |                  |
  |                             |------------------------->|                  |
  |                             |                          | تحقق آلة الحالة   |
  |                             |                          | تحديث ACID        |
  |                             |                          |------------------->|
  |                             |<-------------------------|                  |
  |<----------------------------| نتيجة accepted/conflict  |                  |
```

في حالة التعارض يتوقف المسار قبل تعديل مصدر الحقيقة، ويُنشأ `sync_conflict` وسجل تدقيق. ولا يُعاد تشغيل العملية تلقائيًا إلا إذا كانت السياسة تقول إن الخطأ عابر، مثل انقطاع مؤقت أو `503`، وليس تعارض نسخة أو انتقالًا سريريًا غير مسموح.

## 12. اختبارات قبول API

| الاختبار | النتيجة المطلوبة |
|---|---|
| إرسال العملية نفسها مرتين | سجل واحد ونتيجة `duplicate`. |
| إرسال عمليتين بنفس المفتاح وبحمولتين مختلفتين | `409 IDEMPOTENCY_KEY_REUSE` وتدقيق مخالفة. |
| نسخة قديمة | `409` أو `412` مع `conflict_id` وعدم تعديل الكيان. |
| انتقال غير مسموح | `422` وتسجيل محاولة خرق آلة الحالة. |
| جهاز من مؤسسة أخرى | `403` وعدم كشف وجود السجل. |
| حل تعارض بعد تغير السجل | `412` وإعادة فتح التعارض. |
| دفعة مختلطة | نجاح العمليات السليمة وإرجاع نتيجة مستقلة للعمليات المتعارضة. |
| انقطاع الخادم بعد قبول العملية | إعادة المحاولة تعيد `duplicate` ولا تنشئ أثرًا جديدًا. |
| وصول طارئ مع طابور ممتلئ | حجز سعة أو استجابة واضحة، دون إسقاط العملية بصمت. |
| فشل توقيع الحمولة | `401/403` مع تدقيق، وعدم تخزين العملية كعملية قابلة للتطبيق. |

## 13. قرار التنفيذ في GULA

يُنفذ هذا التصميم كحزمة مستقلة، ولا تُضاف الكتابة إلى `Encounter` أو `Appointment` داخل route جديد. المسارات المقترحة هي:

```text
/api/v1/sync/devices/{device_id}/session
/api/v1/sync/status
/api/v1/sync/operations:batch
/api/v1/sync/operations/{operation_id}:retry
/api/v1/sync/changes
/api/v1/sync/acknowledgements
/api/v1/sync/conflicts
/api/v1/sync/conflicts/{conflict_id}
/api/v1/sync/conflicts/{conflict_id}:resolve
```

وتستدعي طبقة المزامنة الخدمات القائمة الخاصة بالموعد وEncounter وPatient Flow، مع إضافة `sync_operations` و`sync_conflicts` وطبقة worker. لا ينبغي تفعيل الإنتاج قبل إكمال تشفير التخزين المحلي، تسجيل الأجهزة، اختبار الضغط، واختبارات عدم الفقد والتكرار والتعارض.
