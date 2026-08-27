# مصفوفة اختبار Core Appointment Vertical Slice

## سياسة الاختبار

تستخدم الاختبارات بيانات اصطناعية فقط. الاختبارات المحلية سريعة ومشروطة ببيئة `RUNTIME_MODE=test`، بينما اختبار migration وconcurrency متعدد الاتصالات يحتاج PostgreSQL مصرحاً به عبر `MIGRATION_DATABASE_URL`. لا تُستخدم نتائج fixture in-memory لإعلان الجاهزية الإنتاجية.

| الفئة | الحالة المغطاة | الدليل الحالي | النتيجة |
|---|---|---|---|
| Unit | transition `REQUESTED → CONFIRMED` ورفض الانتقال غير الصالح | `test_clinical_core_contracts.py` + service guard | ناجح |
| API | slot/request/confirm/read/list typed routes | `test_core_appointment_api.py` | ناجح محلياً |
| Authorization | session/account/workspace/membership/permission | API fixture و`AppointmentAuthorizationService` | ناجح محلياً |
| IDOR | wrong patient وwrong workspace | `test_core_appointment_api.py` | ناجح محلياً |
| Tenant isolation | organization/facility/workspace filters | service queries وsynthetic cross-scope tests | ناجح جزئياً؛ multi-membership PostgreSQL مطلوب |
| Idempotency | replay نفسه وpayload مختلف | API test | ناجح محلياً |
| Concurrency | lock داخل synthetic وslot unique في DB | `test_synthetic_core_backend.py` | synthetic ناجح؛ multi-worker PostgreSQL مطلوب |
| Audit | success وauthorization denial وoperation rejection | IdentityAuditEntry assertions | ناجح محلياً |
| Rate limit | route limiter و429 envelope | monkeypatch test + global middleware | ناجح contractياً؛ capacity tuning مطلوب |
| Error contract | `VALIDATION_ERROR`, `VERSION_CONFLICT`, `IDEMPOTENCY_CONFLICT`, `CONFLICT`, `FORBIDDEN`, `RATE_LIMITED` | API assertions | ناجح محلياً |
| Migration | tables/columns/FKs/checks/indexes/seeds | `test_core_appointment_migration.py` | skipped محلياً دون PostgreSQL |
| Synthetic E2E | Identity→Session→Workspace→Appointment | 5 synthetic tests | ناجح |
| Frontend contract | Demo/Live boundary | frontend-v3 existing suite | لم يتغير ولم يُفتح write integration |
| Performance | request timing and query path | middleware logs + test duration | measurement seed، لا baseline production |

## Failure Simulation

| سيناريو | السلوك المطلوب | التحقق الحالي |
|---|---|---|
| Network retry/duplicate request | نفس idempotency key يعيد نفس النتيجة | API replay test |
| Expired/revoked session | رفض fail-closed قبل mutation | synthetic revoke test؛ expiry API fixture لاحق |
| Invalid workspace | `FORBIDDEN` دون كشف scope details | API wrong workspace test |
| Unauthorized patient | `FORBIDDEN` ولا يُنشأ appointment | API wrong patient test |
| Slot already taken | `CONFLICT` أو `SLOT_UNAVAILABLE` ولا duplicate | API slot conflict test |
| Concurrent booking | فائز واحد وفشل آمن | synthetic ThreadPool lock؛ PostgreSQL multi-connection لاحق |
| Database rollback | claimed idempotency وslot mutation لا يبقيان عند transaction failure | service transaction design؛ integration fault injection لاحق |
| Partial failure/audit failure | لا يعلن النجاح إن تعذر audit؛ rollback وإشارة correlation | audit commit path؛ fault injection/staging لاحق |
| Stale If-Match | `VERSION_CONFLICT` ورفض silent overwrite | API stale version test |

## Definition of Evidence

نجاح الاختبارات المحلية يثبت contract وsemantics في بيئة الاختبار فقط. لا يُرقّى status إلى `READY_FOR_STAGING` أو `READY_FOR_PRODUCTION` إلا بعد تشغيل migration وsecurity وperformance وrollback على بيئة مصرح بها، ونجاح remote CI وstaging smoke. أي فشل مستقبلي يجب أن يسجل المشكلة والسبب والملفات والتأثير والإصلاح واختبار regression في remediation report.
