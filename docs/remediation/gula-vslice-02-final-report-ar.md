# تقرير تنفيذ Vertical Slice 01B و02 في منصة GULA

**التاريخ:** 27 أغسطس 2026
**المستودع:** [samertts/gula-platform](https://github.com/samertts/gula-platform)
**الفرع:** `feat/citizen-journey-20260827`
**سلسلة commits الوظيفية:** `eced1320` (Slice 02)، `fd2366f7` (migration/locks)، `54d225c1` (evidence)
**PR:** [#250](https://github.com/samertts/gula-platform/pull/250) — مفتوح وDraft

## الملخص التنفيذي

تم تنفيذ الجزء الخادمي من متطلبات الملفين فوق Appointment وNIAM القائمين، من دون إنشاء نظام هوية أو جلسات أو تفويض مكرر، ومن دون فتح كتابات Live في الواجهة. أضيف مسار canonical يبدأ من check-in وينتهي بـEncounter وClinical Note مع state machine وcontextual authorization وidempotency وversion checks وaudit وmigration additive.

كما أدى تشغيل PostgreSQL محلي disposable إلى كشف وإصلاح ثلاثة عيوب حقيقية سابقة في سلسلة Alembic، ثم نجح upgrade إلى الرأس `20260827_0011`، وschema gate، وdowngrade/re-upgrade، وrow-lock proof عبر اتصالين. هذه أدلة تطوير محلية قوية، لكنها لا تساوي staging أو production proof؛ لذلك بقيت حالات `golden_path_passed=false` و`production_ready=false`.

> النتيجة الآمنة: **Vertical Slice 01B/02 منفذ ومختبر محلياً، لكنه غير معتمد للإطلاق الإنتاجي.**

## ما تم تنفيذه

أضيفت حزمة `backend/app/clinical/encounters/` بنماذج `CoreEncounter` و`CoreEncounterQueueEntry` و`CoreClinicalNote`، ومخططات DTO صارمة، وحد authorization، وخدمة domain، ومسارات FastAPI canonical. ينشئ check-in Encounter وQueue entry في transaction واحدة، ويحوّل الموعد المؤكد إلى `CHECKED_IN`. يمنع unique constraint إنشاء Encounter ثانياً لنفس Appointment.

تتبع الزيارة الانتقالات `PLANNED → CHECKED_IN → IN_PROGRESS → COMPLETED`، مع الانتقال الملغى حيث ينطبق. كل mutation حساس يستخدم `Idempotency-Key` و`If-Match` عند الحاجة، وversion conflict، وrow lock، وaudit. دورة Clinical Note هي `DRAFT → COMPLETED → SIGNED`. بعد SIGNED لا يسمح patch مباشر؛ amendment ينشئ version جديداً immutable بحالة `AMENDED` وسبب و`supersedes_id`.

أعيد استخدام `get_current_niam_actor_sync` وNIAM Account/Session/Workspace/Membership/Role/Permission و`AppointmentAuthorizationService` و`SyncCanonicalAuditService`. لا تمنح role أو workspace المرسل من frontend صلاحية، ولا تدخل national/health IDs أو tokens في DTOs الجديدة. بقي Demo synthetic/read-only/isolated.

أضيفت migration `20260827_0011_core_encounter_note_slice.py` لجداول Encounter وQueue وClinical Note مع FKs وchecks وunique/indexes وpermission seeds، من دون حذف الجداول legacy. كما وُسع workflow `.github/workflows/iam-hardening.yml` ليشمل schema gate وrow-lock proof وcontract tests مع artifacts.

## إصلاحات migration chain المكتشفة بالدليل الفعلي

أثناء تشغيل قاعدة PostgreSQL نظيفة ظهر أن `507ea11c820a` كان ينشئ index باسم سبق أن أنشأته `20260503_0001`; أضيف existence guard، وأصبح downgrade لا يسقط index المملوك للـrevision السابقة. وظهر أن drug substitution يستخدم `VARCHAR(26)` مع FK إلى `pharmacy_drug_catalog.id` من نوع INTEGER؛ تمت مواءمة حقلي FK إلى Integer.

كما كشف upgrade أن `20260820_0007` ينشئ FK إلى `hospital_operation_theaters` من دون أن تكون DDL لذلك الجدول موجودة في السلسلة. أضيف DDL مشروط لـ`hospitals` و`hospital_departments` و`hospital_operation_theaters` وفق ORM canonical، مع إبقاء parent resources في downgrade لحماية أي بيانات تشغيلية. هذه الإصلاحات غير تدميرية في قاعدة تحتوي الجداول مسبقاً، ولا تنفذ حذفاً تلقائياً للـparent resources.

## الأدلة والاختبارات

| الدليل | النتيجة | الحدود |
|---|---:|---|
| Full backend suite الحالي | `2794 passed, 5 skipped, 165 warnings`، `exit code=0`، خلال `322.58s` | محلي؛ التحذيرات موثقة ولم تُخفَ |
| Focused Slice 02 suite | `35 passed, 1 skipped` | local contract/read-gate/migration-chain |
| PostgreSQL upgrade | وصل إلى `20260827_0011 (head)` | PostgreSQL 16.15 disposable محلي |
| PostgreSQL schema gate | `1 passed` | لا يمثل staging |
| PostgreSQL rollback | downgrade إلى `20260814_0002` ثم upgrade إلى head نجح | parent Hospital بقي عمداً |
| Row-lock proof | `winner, conflict` عبر اتصالين | database primitive، وليس API worker-load test |
| Frontend v3 المحلي | test/lint/typecheck/build/bundle budget ناجحة | لم تتغير frontend files ولم تُفتح Live writes |
| Ruff/compile/YAML/JSON/diff-check | ناجحة | نطاق الملفات المعدلة |

الاختبار المتجاوز محلياً في focused suite هو schema gate عند تشغيله من harness الاختباري دون `MIGRATION_DATABASE_URL`. أما PostgreSQL proof الفعلي فقد شُغل بصورة مستقلة على قاعدة disposable محلية ونجح.

## الأمن والتفويض وسلامة البيانات

كل check-in وEncounter وNote write يمر عبر session/account/identity/workspace/membership/permission وorganization/facility/workspace object scope. patient self-access لا يُستنتج من frontend. provider access مشروط بعضوية نشطة وصلاحية scoped. الأخطاء الآمنة لا تكشف سبب العضوية أو facility التفصيلي.

لا يوجد silent overwrite. stale `If-Match` يرفض العملية، وsigned note لا يعدّل مباشرة، وamendment منفصل ومدقق. receipts تحفظ fingerprint وresponse replay، وتستخدم `resource_id` polymorphic. audit يمر عبر hash-chain NIAM القائم ويسجل success وdenial وrejection مع actor/scope/target/correlation IDs، من دون password أو access/refresh token أو PHI غير اللازمة.

## Architectural drift وEngineering Intelligence

أصبح `app/national/domain/facility.py` هو canonical owner لـ`national_facilities`. أزيل ORM duplicate من `clinical_scope.py`، وبقي bridge opaque وFK enforcement في migration حيث تفصل SQLAlchemy metadata بين Base وIdentityBase. لم تُحذف جداول legacy ولم يُربط المسار الجديد بـNational Scheduling admin/raw route.

تم توسيع Engineering Inventory ليكشف missing Encounter/Note contract evidence وmigration/evidence gaps. التقرير advisory؛ نتيجة inventory لا ترقي النظام إلى production. كما وثق `backend-warning-inventory-ar.md` التحذيرات الـ165 بحسب owner/type بدلاً من suppression شامل.

## Remote CI وحالة GitHub

بعد commit `54d225c1` بدأ GitHub Actions runs جديدة لـIAM Hardening وFrontend Bundle Budget، لكن كلاهما انتهى `failure`. metadata أظهرت أن jobs فشلت خلال ثوانٍ وجميعها بلا steps قابلة للقراءة، وسجلات job أعادت `BlobNotFound`. لذلك لم أعتبر remote CI أخضر، ولم أغيّر حالة الجاهزية. الاختبارات المقابلة محلياً نجحت: backend identity `205 passed, 5 deselected`، security/tenant `76 passed`، وfrontend test/lint/typecheck/build/bundle budget نجحت.

هذا يبقي remote CI **external/unresolved** وليس فشلاً وظيفياً مثبتاً في الكود. يلزم تشغيل GitHub Actions بصلاحية logs/runner صحيحة أو فحص إعدادات billing/runner من مالك المستودع قبل الاعتماد على نتيجة بعيدة.

## Dependabot

ما زال Dependabot alert **#471** يعرض vulnerability واحدة moderate على default branch، وفق رسالة GitHub أثناء الدفع. محاولة القراءة التفصيلية أعادت `403 Resource not accessible by integration`. لم يتم dismiss أو suppress، ولم تُخلط معالجة Netty/Android في commit السريري.

## ما لم يُنفذ عمداً

لم تُفتح كتابات Live في `frontend-v3`، ولم تُربط `/app/appointments` أو أي شاشة clinical بكتابات جديدة. لم يُفتح Encounter أو Note للمستخدمين الحقيقيين. لم تُنفذ staging smoke أو rollback على بيئة تشغيلية أو browser E2E عبر حساب حقيقي. لم تُضف integrations حكومية أو HIS/LIS/RIS/PACS أو SMS/Telegram/WhatsApp أو payment/insurance أو بيانات مواطنين حقيقية.

لا توجد بعد قياسات p50/p95/p99 أو query-count أو memory/CPU تحت حمل production-like، ولا proof متعدد العمال عبر API/Redis. row-lock proof المحلي لا يغلق هذه الفجوة وحده. كما لا توجد مراجعة مستقلة للـauthorization/audit أو data retention في staging.

## Rollback وخطة الخطوة التالية

الـrollback المحلي المثبت هو downgrade إلى `20260814_0002` ثم re-upgrade إلى `20260827_0011`. migration 0010 و0011 additive، وdowngrade الخاص بـ0011 يحذف جداول slice فقط. إصلاحات parent Hospital تتعمد الاحتفاظ بالـparent في downgrade حتى لا تحذف بيانات تشغيلية. أي deployment حقيقي يحتاج backup وapproval وrollback rehearsal مستقلين.

الخطوة التالية الآمنة هي معالجة سبب فشل remote CI من خلال مالك GitHub/runner، ثم تشغيل migration/schema gate وAPI integration وconcurrency تحت PostgreSQL/Redis في بيئة معزولة قابلة للوصول. بعد نجاح ذلك فقط يُبنى read-only frontend adapter، ثم feature flag محدود للكتابات مع browser E2E وaudit/rollback evidence. لا ينبغي فتح pharmacy أو imaging أو hospital أو emergency قبل قبول هذا المسار.

## حالة التسليم

الفرع نظيف ومرفوع إلى `origin/feat/citizen-journey-20260827`، وHEAD النهائي يُتحقق منه في PR #250. PR #250 مفتوح وDraft فوق `fix/external-ingestion-dmz-er-20260825`. لم يحدث merge أو force push أو deployment أو store submission.

### المراجع

[1]: https://github.com/samertts/gula-platform/pull/250 "GULA PR #250"
[2]: https://github.com/samertts/gula-platform/actions/runs/33112384433 "IAM Hardening Gate run for commit 54d225c1"
[3]: https://github.com/samertts/gula-platform/actions/runs/33112384425 "Frontend Bundle Budget run for commit 54d225c1"
[4]: https://github.com/samertts/gula-platform/security/dependabot/471 "Dependabot alert #471"
