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
| Domain/model/state machine | `BUILDING` | models و`clinical_core.py` واختبارات transition |
| API/error contract | `TESTING` | typed DTOs وFastAPI routes وAPI tests |
| Authorization/tenant/IDOR | `TESTING` | workspace/membership/object filters وnegative tests |
| Idempotency/version | `TESTING` | replay وpayload conflict وstale If-Match tests |
| Audit | `TESTING` | CanonicalAuditService وassertions على denial/success |
| Synthetic Golden Path | `TESTING` | 5 synthetic tests و6 API tests تشمل context/session/error/rate-limit |
| Full backend regression | `LOCAL_PASS` | `2791 passed, 5 skipped, 165 warnings`، exit code `0` من الشجرة النهائية |
| Migration | `EXTERNAL_DEPENDENCY` | migration موجودة، تحقق PostgreSQL مشروط بـ`MIGRATION_DATABASE_URL` |
| Engineering Inventory | `TESTING` | `backend/scripts/engineering_inventory.py` يصدر JSON advisory عن routes/models/migration/evidence gaps |
| Performance | `IMPROVING` | request timing logs؛ لا يوجد baseline PostgreSQL متعدد العمال بعد |
| Frontend integration | `DISCOVERED` | allowlist لم تُفتح، Demo بقي read-only |
| Remote CI/staging/rollback | `EXTERNAL_DEPENDENCY` | صلاحيات وبيئات خارجية مطلوبة |

## ما لم يُنفذ عمداً

لم تُربط `/app/appointments` بكتابات Live بعد، ولم تُفتح pharmacy أو imaging أو hospital أو emergency أو insurance. لم تُنشأ طبقة Device production جديدة لأن NIAM device/session audit قائم ويحتاج audit end-to-end مستقل. لم تُنفذ login/refresh/rotate جديدة، ولا integrations حكومية أو HIS/LIS/RIS/PACS أو SMS/Telegram أو بيانات مواطنين حقيقية.

نجاح full backend suite المحلي لا يثبت وحده أن migration تعمل على PostgreSQL، ولا يثبت in-memory synthetic backend أن الخدمة صالحة للإنتاج. ما يزال يلزم اختبار concurrency حقيقي متعدد الاتصالات، rate-limit 429 قابل لإعادة الإنتاج تحت حمل production-like، مراجعة أمنية بعيدة وremote CI، staging smoke، وrollback موثق ومجرب قبل أي promotion.

## Regression Memory

| المشكلة المكتشفة | السبب الجذري | الإصلاح | اختبار الرجوع |
|---|---|---|---|
| فشل audit insert | `IdentityAuditEntry.uuid` مطلوب بلا default في adapter | إضافة UUID صريح في async/sync canonical audit | Golden API يثبت slot audit والـdeny audit |
| 500 عند session في SQLite | timestamp صار naive بعد persistence | تطبيع session expiry إلى UTC قبل المقارنة | API Golden Path |
| error code عام في الاختبار | `HTTPException` dict يعاد إلى handler كـ`Request failed` | استخدام `DomainError` مع explicit code/details | stale `If-Match` assertion |
| mapper failure بعد cross-metadata FK | Base وIdentityBase منفصلان | نقل FK enforcement إلى migration مع توثيق السبب | إنشاء SQLite + API tests |
| تسرب permissions أو rollback بين اختبارات API | commit داخل TestClient مع savepoint غير مضبوط، وfixture يعيد إدخال permission | session/savepoint مستقل لكل request، وpermission fixture idempotent، والتقاط scalar IDs بعد rollback | تشغيل auth وappointment suites معاً ثم full backend suite |

## القرار التالي

بعد مراجعة هذه الموجة، القرار الآمن هو تشغيل migration test على PostgreSQL مصرح به، ثم اختبار worker concurrency وrate-limit failure وrollback. فقط إذا نجحت هذه الأدلة يمكن إعداد adapter read-only أولاً لـ`/app/appointments`، مع إبقاء Demo معزولاً، ثم فتح write integration تدريجياً بfeature flag وcontract tests. لا يُستخدم لفظ `GOLDEN PATH PASSED` أو `PRODUCTION READY` قبل اكتمال مصفوفة الأدلة البعيدة والبيئة الواقعية.
