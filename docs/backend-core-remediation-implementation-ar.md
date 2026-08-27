# Backend Core Remediation وAppointment Vertical Slice

## النطاق والقاعدة التشغيلية

تُوثّق هذه الوثيقة الموجة الحالية من Backend Remediation بعد تأسيس `frontend-v3`. الغرض هو بناء أول vertical slice خادمي حقيقي يبدأ من **Account/Identity/Session/Workspace/Membership/Permission** وينتهي بطلب موعد وتأكيده، مع استخدام بيانات اصطناعية في الاختبارات فقط. لا تمنح هذه الموجة أي واجهة أمامية صلاحية سريرية، ولا تُحوّل Demo إلى fallback، ولا ترفع العقد إلى `READY_FOR_PRODUCTION` دون أدلة بعيدة وبيئة staging وrollback.

> الحواجز هنا أدوات تشخيص وحماية للبيانات، وليست آلية لتجميد التطوير. في حالات الغموض نستخدم `DOCUMENT → COMPARE → SELECT REVERSIBLE OPTION → IMPLEMENT → TEST`.

## ما تم تنفيذه

أُضيفت حزمة `backend/app/clinical/appointments/` كمسار canonical منفصل عن `National Scheduling` القديم. تحتوي على ORM models وDTOs وauthorization boundary وdomain service وFastAPI router. المسار لا يعيد استخدام router الإداري القديم مباشرة، ولا يسمح للعميل باختيار organization أو facility من دون أن يطابق ذلك سياق membership/workspace الذي يشتقه الخادم.

الجداول الجديدة هي `core_appointment_slots` و`core_appointments` و`core_appointment_idempotency`. أُضيفت migration additive بالـrevision `20260827_0010`، وتشمل foreign keys على جداول NIAM، unique slot/provider window، unique appointment per slot، check constraints للحالة والزمن، وفهارس scope/provider/patient/idempotency. لم تُحذف جداول National Scheduling ولم تُنفذ إعادة ضبط أو migration تدميرية.

| العملية | العقد الخادمي | ضوابط الكتابة |
|---|---|---|
| إنشاء slot | `POST /api/v1/appointments/slots` | workspace membership، provider scope، permission، idempotency، unique window، audit |
| طلب موعد | `POST /api/v1/appointments` | session، workspace، self-patient، provider scope، slot lock، idempotency، unique slot، audit |
| تأكيد موعد | `POST /api/v1/appointments/{appointment_id}/confirm` | permission، tenant/object scope، `If-Match`، state transition، idempotency، audit |
| قراءة موعد | `GET /api/v1/appointments/{appointment_id}` | organization/facility/workspace filter، requester/provider أو permission |
| قائمة المواعيد | `GET /api/v1/appointments` | scoped query، pagination، owner/provider visibility عند غياب read permission |
| قائمة الفترات | `GET /api/v1/appointments/slots` | scoped query، time filtering، pagination، available-only |

## Vertical Slice 02 — Check-in وEncounter وClinical Note

أُضيفت حزمة `backend/app/clinical/encounters/` كمسار canonical منفصل. ينشئ `POST /api/v1/encounters/check-in` Encounter وQueue entry بحالة `CHECKED_IN/WAITING` داخل transaction واحدة، ثم يدعم `start` و`complete` مع `If-Match` وidempotency وprovider/object authorization. لا يسمح المسار بإنشاء Encounter مزدوجاً لنفس Appointment بسبب unique constraint وrow lock.

يدعم Clinical Note إنشاء `DRAFT`، والتحديث بإصدار متوقع، و`COMPLETED` و`SIGNED`، ثم amendment immutable بحالة `AMENDED` و`supersedes_id` وسبب إلزامي. لا يوجد تعديل مباشر بعد SIGNED. كل العمليات تمر عبر `SyncCanonicalAuditService`، وتستخدم صلاحيات `encounter.checkin`, `encounter.manage`, `encounter.read`, `clinical.note.write`, `clinical.note.sign`, و`clinical.note.amend` ضمن scope.

أُضيفت migration additive `20260827_0011_core_encounter_note_slice.py` لجداول `core_encounters` و`core_encounter_queue` و`core_clinical_notes` مع FKs وchecks وunique/indexes. بقيت الجداول legacy دون حذف. واختير `app.national.domain.facility.Facility` كـcanonical owner لـ`national_facilities`، وأزيل ORM duplicate من `clinical_scope.py` مع إبقاء bridge opaque وFK migration-only.

## Identity وSession وWorkspace

تُعاد الاستفادة من NIAM القائم عبر `get_current_niam_actor_sync` و`Account` و`UserSession` و`WorkspaceSessionContext` و`Membership` و`RoleAssignment` و`RolePermission`. يتحقق `AppointmentAuthorizationService` من نشاط الحساب والجلسة وعدم انتهائها، ومن تطابق session مع account، ومن workspace context، ومن نشاط organization/facility/workspace/membership، ومن permission المرتبطة بـrole داخل scope.

لا تدخل `national_id` أو `health_id` أو `device_fingerprint` في نموذج الموعد أو response. تستخدم identifiers داخلية opaque، ويُحفظ session UUID في audit فقط. عند رفض التفويض يُسجل سبب داخلي bounded، بينما يعيد العميل `FORBIDDEN` دون كشف هل كان السبب عضوية أو منشأة أو علاقة مريض.

## State Machine

الحالة canonical هي `REQUESTED → CONFIRMED` ضمن هذا vertical slice، مع اعتماد الحالات المستقبلية المسجلة في `clinical_core.py`: `CHECKED_IN` و`IN_PROGRESS` و`COMPLETED` و`CANCELLED` و`NO_SHOW` و`RESCHEDULED` و`EXPIRED`. يستخدم service `require_transition("appointment", ...)` ولا يسمح بتأكيد حالة ليست `REQUESTED`. أي إلغاء أو إعادة جدولة لاحقة يجب أن تكون command مستقلة بانتقال رسمي، وليس تحديثاً عاماً أو Last Write Wins.

## Idempotency وConcurrency

تُخزن مفاتيح idempotency في قاعدة البيانات داخل نطاق `actor_account_id + operation + idempotency_key` مع fingerprint للـpayload وresponse محفوظة عند النجاح. إعادة إرسال payload نفسه يعيد نفس appointment أو slot، بينما إعادة استخدام المفتاح مع payload مختلف تعيد `IDEMPOTENCY_CONFLICT`. إذا كان الطلب قيد المعالجة لا يُنشأ side effect ثانٍ.

يُقفل slot عبر `SELECT ... FOR UPDATE` أثناء طلب الموعد، وتوجد unique constraint على slot في appointment وعلى نافذة provider في slot. يستخدم confirm `If-Match` مع version ويعيد `VERSION_CONFLICT` عند stale update. SQLite الاختباري يثبت semantics، أما إثبات concurrency متعدد العمال في PostgreSQL فيبقى شرطاً قبل staging.

## Audit وError Contract وRate Limit

تستخدم الخدمة `SyncCanonicalAuditService` نفسه المستخدم في NIAM، مع UUID صريح وسجل hash-chain قائم بدلاً من إنشاء audit store ثانٍ. تُسجل أحداث `APPOINTMENT_SLOT_CREATED` و`APPOINTMENT_REQUESTED` و`APPOINTMENT_CONFIRMED`، كما تُسجل حالات الرفض والتعارض على أنها `APPOINTMENT_AUTHORIZATION_DENIED` أو `APPOINTMENT_OPERATION_REJECTED`. يحمل الحدث actor وorganization وfacility وworkspace وtarget وaction وdecision وrequest/correlation IDs وbefore/after عند الانتقال، ولا يحمل password أو access token أو refresh token أو PHI غير الضروري.

تستفيد المسارات من `rate_limit_user` بالإضافة إلى global middleware. الاستجابات تمر عبر error contract المركزي في `factory.py` وتحافظ على code في المستوى الأعلى و`detail` legacy النصي للتوافق. لا تُعاد stack traces؛ التشخيص التفصيلي يبقى في logs المحلية ولا يتضمن أسراراً.

## Synthetic Test Backend

وُسّع `backend/tests/fixtures/synthetic_core_backend.py` ليحاكي Identity وSession وWorkspace وMembership وAppointment، مع دعم session revoke، membership scope، idempotency، state transitions، audit، وlock حقيقي داخل العملية لتجربة سيناريوهات التزامن. يبقى هذا fixture test-only وin-memory ولا يستورد persistence production ولا يثبت readiness الإنتاجية.

## Evidence الحالية

| البند | الحالة | الدليل |
|---|---|---|
| Architecture reconciliation | `READY_FOR_REVIEW` | ADR والخريطة بين National Scheduling وcanonical model |
| Domain/model/state machine | `TESTING` | models و`clinical_core.py` واختبارات Appointment وEncounter/Note transition |
| API/error contract | `TESTING` | typed DTOs وFastAPI routes لـAppointment وEncounter/Note وAPI tests |
| Authorization/tenant/IDOR | `TESTING` | workspace/membership/object filters وnegative tests |
| Idempotency/version | `TESTING` | replay وpayload conflict وstale If-Match tests |
| Audit | `TESTING` | CanonicalAuditService وassertions على denial/success |
| Synthetic Golden Path | `TESTING` | 5 synthetic tests و6 Appointment API tests و3 Encounter/Note API tests تشمل context/session/error/rate-limit |
| Slice 02 focused regression | `LOCAL_PASS` | 35 passed، 1 skipped، ويشمل Encounter/Note وAppointment وcontracts وread-gate وmigration-chain |
| Full backend regression | `LOCAL_PASS` | `2797 passed, 5 skipped, 165 warnings in 308.37s`، وexit code `0` ملتقط من الشجرة النهائية بعد Redis hardening وmigration guard 0012 |
| Migration | `LOCAL_POSTGRES_PASS` | upgrade head إلى 0012 وschema gate وdowngrade/re-upgrade نجحت على PostgreSQL 16.15 disposable؛ guard يرفض drift غير الآمن ولا ينفذ casts؛ remote/staging proof ما زال مطلوباً |
| Engineering Inventory | `TESTING` | `backend/scripts/engineering_inventory.py` يصدر JSON advisory عن routes/models/migration/evidence gaps |
| Performance | `IMPROVING` | request timing logs؛ row-lock proof عبر اتصالين وRedis shared-controls proof عبر processes، ولا يوجد API/worker load baseline بعد |
| Frontend integration | `DISCOVERED` | allowlist لم تُفتح، Demo بقي read-only |
| Redis production control | `LOCAL_PASS` | fail-closed policy عند outage واختبار shared counter/revocation عبر processes؛ Redis الإنتاجي وHA وobservability ما زالت خارج الدليل |
| Remote CI/staging/rollback | `EXTERNAL_DEPENDENCY` | local PostgreSQL وRedis proofs نجحت، لكن remote CI الحالي ما زال فاشلاً؛ staging smoke وrollback التشغيلي ما زالا مطلوبين |

## ما لم يُنفذ عمداً

لم تُربط `/app/appointments` بكتابات Live بعد، ولم تُفتح pharmacy أو imaging أو hospital أو emergency أو insurance. لم تُنشأ طبقة Device production جديدة لأن NIAM device/session audit قائم ويحتاج audit end-to-end مستقل. لم تُنفذ login/refresh/rotate جديدة، ولا integrations حكومية أو HIS/LIS/RIS/PACS أو SMS/Telegram أو بيانات مواطنين حقيقية.

نجاح full backend suite المحلي لا يثبت وحده أن الخدمة صالحة للإنتاج. أصبح لدينا الآن PostgreSQL disposable proof وrow-lock proof وRedis shared-controls proof، لكن ما يزال يلزم API/worker contention تحت حمل production-like، rate-limit 429 capacity، Redis HA/failover، مراجعة أمنية بعيدة وremote CI، staging smoke، وrollback موثق ومجرب قبل أي promotion.

## Regression Memory

| المشكلة المكتشفة | السبب الجذري | الإصلاح | اختبار الرجوع |
|---|---|---|---|
| فشل audit insert | `IdentityAuditEntry.uuid` مطلوب بلا default في adapter | إضافة UUID صريح في async/sync canonical audit | Golden API يثبت slot audit والـdeny audit |
| 500 عند session في SQLite | timestamp صار naive بعد persistence | تطبيع session expiry إلى UTC قبل المقارنة | API Golden Path |
| error code عام في الاختبار | `HTTPException` dict يعاد إلى handler كـ`Request failed` | استخدام `DomainError` مع explicit code/details | stale `If-Match` assertion |
| mapper failure بعد cross-metadata FK | Base وIdentityBase منفصلان | نقل FK enforcement إلى migration مع توثيق السبب | إنشاء SQLite + API tests |
| فشل migration بسبب duplicate index | migration 507ea11c820a أنشأت اسماً مملوكاً لـ20260503_0001 بلا guard | إضافة index existence guard وعدم إسقاط index المملوك سابقاً | PostgreSQL disposable upgrade |
| فشل drug substitution FK | VARCHAR FK إلى pharmacy_drug_catalog.id من نوع INTEGER | مواءمة rule FK columns إلى Integer | PostgreSQL disposable upgrade |
| فشل OperationTheater dependency | جدول ORM موجود بلا DDL في migration chain | إصلاح fresh-chain التاريخي، ثم forward guard 0012 يتحقق من وجود parents وFK عند وجود checklist ولا ينشئ schema إنتاجياً تخمينياً | PostgreSQL upgrade + rollback/re-upgrade |
| drift في deployed schema بعد تعديل migration تاريخية | قواعد سبق أن سجلت revision لا تعيد تشغيل الملف التاريخي | إضافة `20260827_0012` كـforward compatibility guard: يعيد فهرساً مفقوداً فقط، ويفشل مغلقاً عند FK/type/parent drift مع طلب data/DDL review | fresh upgrade إلى 0012 + downgrade/re-upgrade |
| تسرب permissions أو rollback بين اختبارات API | commit داخل TestClient مع savepoint غير مضبوط، وfixture يعيد إدخال permission | session/savepoint مستقل لكل request، وpermission fixture idempotent، والتقاط scalar IDs بعد rollback | تشغيل auth وappointment suites معاً ثم full backend suite |

## القرار التالي

بعد مراجعة هذه الموجة، القرار الآمن هو تشغيل migration test على PostgreSQL مصرح به، ثم اختبار worker concurrency وrate-limit failure وrollback، مع مراجعة أي drift يوقفه guard 0012 يدوياً قبل cast أو DDL إصلاحي. فقط إذا نجحت هذه الأدلة يمكن إعداد adapter read-only أولاً لـ`/app/appointments`، مع إبقاء Demo معزولاً، ثم فتح write integration تدريجياً بfeature flag وcontract tests. لا يُستخدم لفظ `GOLDEN PATH PASSED` أو `PRODUCTION READY` قبل اكتمال مصفوفة الأدلة البعيدة والبيئة الواقعية.
