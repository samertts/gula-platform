# تقرير تنفيذ FIX ALL — منصة GULA

**التاريخ:** 22 أغسطس 2026
**الفرع:** `fix/main-migration-graph-20260822`
**النطاق:** إصلاح الأعطال القابلة للتنفيذ على أساس `origin/main`، مع الحفاظ على متطلبات السلامة الطبية والأمنية وعدم تحويل التحذيرات الحقيقية إلى نجاح زائف.

## الملخص التنفيذي

تم تنفيذ جولة FIX ALL على نسخة عمل مستقلة مبنية من `origin/main` الحالي. شملت الجولة إصلاح رسم migrations في Alembic، معالجة regression في `frontend-v3`، استبدال الاستخدامات المباشرة لـ `datetime.utcnow()` بتواريخ UTC-aware، وإصلاح أخطاء أسماء ظهرت أثناء التحقق الثابت. أُعيد تشغيل اختبارات backend وfrontend وبوابات الجودة الأساسية، وجميعها نجحت باستثناء أن **Data Preservation Gate ما زالت تعيد WARNING حقيقية** بسبب فجوة soft-delete في نماذج legacy؛ لم يتم إخفاء هذا التحذير أو ادعاء أن Rule 10 أُصلحت بنيوياً.

لا تتضمن هذه الجولة migration شاملة لإضافة حقول soft-delete إلى جداول الأعمال المحمية، لأن ذلك تغيير schema يتطلب موافقة Architecture Board وخطة backup/rollback وترحيل تدريجية. كما لم تُعدّل إعدادات GitHub billing أو Vercel أو Dependabot، لأنها عوائق تشغيلية خارج المستودع وليست إصلاحات كود.

## الإصلاحات المنفذة

| المجال | الإصلاح | النتيجة |
|---|---|---|
| Alembic | إعادة ترقيم وربط migrations المتعارضة: `clinical_command_receipts` إلى `20260820_0006`، و`surgical_safety_checklists` إلى `20260820_0007`، و`icu_infusion_independent_verification` إلى `20260820_0008`. | أصبح للرسم رأس واحد هو `20260820_0008`. لم يتغير منطق الجداول أو عمليات upgrade/downgrade، بل عولج التعارض في revision graph فقط. |
| Frontend accessibility | تصحيح `MobileBottomNav` ليستخدم `mobileNav.openAllSections` في `aria-label` و`title`، مع إبقاء النص المرئي `mobileNav.more` وسلوك `aria-expanded`. | عادت اختبارات MobileBottomNav للعمل، واجتازت مجموعة frontend كاملة. |
| UTC handling | تحويل استدعاءات `datetime.utcnow()` و`UTC.utcnow()` المباشرة في نطاق backend/shared/services/edge_agent والسكربتات ذات الصلة إلى `datetime.now(UTC)` أو `datetime.now(timezone.utc)`، مع الحفاظ على `default_factory` وSQLAlchemy callables lazy. | لا توجد مراجع مباشرة متبقية لـ `datetime.utcnow()` أو `UTC.utcnow()` في النطاق المفحوص. |
| Generated code | تحديث قالب repository generator ليستورد UTC وdatetime ويولد `datetime.now(UTC)`، مع إبقاء الاستيرادات بعد `from __future__` صحيحة. | نجح compileall واختبار المسارات المتأثرة. |
| Scripts | إصلاح import datetime المفقود في `compliance_reporter.py`، وتحويل timestamp إلى UTC-aware، وتحديث `integration_test.sh` و`generate_demo_data.py`. كما أُصلح `Lab` غير المعرّف داخل `_create_users`. | نجح فحص Ruff F821 وcompileall. |
| جودة الكود | إزالة imports UTC المكررة التي كشفها Ruff في `idempotency.py` و`outbox_service.py`. | بوابة `ruff check backend/app --select E9,F --ignore F401,F841` ناجحة. |

## نتائج التحقق

| البوابة | النتيجة المثبتة |
|---|---|
| Backend full suite | **2727 passed, 4 skipped, 21 warnings** خلال نحو 230 ثانية بعد الإصلاحات الجديدة. |
| Alembic | `20260820_0008 (head)`؛ رأس واحد فقط. |
| Migration tests | **9 passed, 1 warning**. |
| Python compilation | `python -m compileall -q backend shared services edge_agent scripts` ناجح. |
| Ruff | ناجح بعد معالجة F811 وF821 في الملفات المتأثرة. |
| Frontend installation | `npm ci --ignore-scripts` ناجح باستخدام lockfile المتتبع. |
| Frontend quality | `npm run lint` و`npm run typecheck` ناجحان. |
| Frontend tests | **16 test files و56 tests passed**. |
| Frontend build | `npm run build` ناجح وولّد PWA assets. |
| Frontend production audit | `npm audit --omit=dev`: **0 vulnerabilities**؛ المعلومات كانت `info=0, low=0, moderate=0, high=0, critical=0`. |
| Direct UTC search | لا توجد مراجع مباشرة لـ `datetime.utcnow()` أو `UTC.utcnow()` في backend/shared/services/edge_agent/scripts بعد الإصلاح. |

التحذيرات الـ21 في backend ليست نجاحاً زائفاً مخفياً؛ مصدرها الظاهر هو توافق Starlette/TestClient، تكامل Sentry، محول SQLite datetime في Python 3.12، وتحذير حجم مفتاح jose داخل اختبار أمني مقصود. لم تُستخدم آلية لإسكات الاختبارات أو تجاوز فشل أمني.

## حدود Data Preservation وRule 10

تم تحسين `scripts/data_preservation_gate.py` من heuristic على مستوى الملف إلى AST inventory على مستوى class/table، مع اكتشاف `__tablename__`، والحقول المباشرة، والوراثة من `SoftDeleteMixin`، وتصنيف append-only/transient/business. كما تمت إضافة جميع الجداول المكتشفة إلى Protected Tables Registry، وإضافة `--strict` ليحوّل فجوات Rule 10 الحقيقية إلى **FAIL / exit 2** عند فحص جاهزية الإنتاج، مع إبقاء الوضع الافتراضي **WARNING / exit 1** لمسار remediation.

النتيجة الحالية: **68 model classes inventoried، ولا توجد جداول unregistered، و61 business model ما زالت تفتقد soft-delete support**. صُنفت `audit_logs` و`outbox_events` و`authorization_audit` و`clinical_command_receipts` و`edge_events` كسجلات append-only، وصُنفت `mfa_sessions` و`oauth2_tokens` كمخازن تشغيلية منتهية/قابلة للإبطال. هذه التصنيفات لا تمنح صلاحية حذف؛ بل تتطلب retention وintegrity وaccess controls موثقة.

الوضع الافتراضي يعيد `WARNING / exit 1`، والوضع `python scripts/data_preservation_gate.py --ci --strict` يعيد **FAIL / exit 2** كما يجب، لأن إضافة الأعمدة وحدها لا تثبت default query filtering أو restore authorization. لم تُضف migration إلى الجداول المحمية. أضيف ADR-026 يثبت خطة rollout، ويلزم قبل أي schema change موافقة Architecture Board، وbackup/checksum/clone restore، وتسلسل expand/validate/switch، واختبارات tenant isolation والعلاقات والـrollback.

## إصلاحات الأمن الإضافية

أُزيلت بيانات PII وكلمات المرور الثابتة من التنفيذ الافتراضي في `gula_citizen_portal.py` و`gula_registration_portal.py`. أصبحت أمثلة SQLite تستخدم PBKDF2 مع salt عشوائي وتنسيق hash versioned، وترفض legacy SHA-256، وتتطلب المصادقة قبل إضافة سجل طبي، ولا تشغّل demo credentials تلقائياً. كما تحسن `.audit/scan_secrets_safe.py` لتمييز مراجع environment والـdocumentation headers، واكتشاف PEM فعلي، وتصنيف fixtures الاختبارية دون إخفائها.

نتيجة فحص الأسرار بعد التعديل: **17 findingاً إجمالاً، 0 non-placeholder findings، و9 test-fixture-like findings**. هذا لا يلغي الحاجة إلى secret scanning في GitHub ومراجعة التدوير الفعلي للمفاتيح في بيئة الإنتاج؛ لكنه يزيل القيم literal التي كانت موجودة في الأمثلة المنفردة.

> الاستنتاج التشغيلي: تحسن الكاشف وأصبح يخرج inventory قابلاً للتدقيق، لكن Rule 10 لم تُغلق schema-wise بعد. لا يجوز اعتبار strict gate ناجحاً أو استخدام استثناء غير موثق لتجاوز الفجوة.

## متطلبات السلامة التي لم تُمس

لم تغيّر الإصلاحات semantics الخاصة بالمسارات السريرية أو الأمن. بقيت المسارات غير المنفذة وغير المهيأة خاضعة لعقود الفشل المطلوبة، ولم يُحوّل أي endpoint إلى نجاح 2xx زائف. بقيت مخرجات AI ضمن advisory-only، وتكاملات Wearables ضمن simulation-only، كما لم تُزل ضوابط `lab_id` لعزل المستأجرين أو state-machine وaudit وidempotency وoptimistic locking. لم تُستخدم هذه الجولة لإضافة حذف فعلي للبيانات أو تجاوز صلاحيات أو إخفاء فشل CI.

## عوائق خارجية غير قابلة للإصلاح من الكود

| العائق | أثره | الإجراء المتخذ |
|---|---|---|
| GitHub Actions billing/spending-limit | بعض CI المنشور سابقاً لم يبدأ التنفيذ أو ظهر غير مستقر بسبب حساب GitHub. | لم يتم تغيير billing أو spending limit؛ يجب على مالك الحساب معالجة الإعدادات ثم إعادة تشغيل checks. |
| Vercel account/team verification | فشل نشر سابق مرتبط بالتحقق من الحساب/الفريق، لا بخطأ build المحلي. | لم يتم تجاوز التحقق أو تغيير إعدادات الحساب. |
| Dependabot #471 — Netty moderate | يحتاج تحققاً حديثاً على مستوى GitHub بعد إصلاحات Android السابقة. | لم يتم dismiss للتنبيه ولم يُعلن إغلاقه دون scan حديث. |
| Rule 10 | WARNING بنيوي يحتاج Architecture Board approval. | بقي ظاهراً كما هو، مع عدم تنفيذ schema change غير معتمد. |

## الخطوة التالية

يجب مراجعة تغييرات Rule 10 والأمن في PR مستقل أو تحديث PR الإصلاح الحالي، ثم تقييم CI المنشور مع التمييز بين فشل job فعلي وفشل pre-execution بسبب billing أو Vercel. لا يُغلق PR أو يُدمج إلى `main` قبل مراجعة strict gate، واعتماد خطة schema المستقلة، وتوقيعات Architecture وSecurity وPrivacy وQA/Validation وOperations والقيادة السريرية.


## متابعة تنفيذ Rule 10 والأمن — الجولة الحالية

تم استبدال فحص Rule 10 القائم على regex على مستوى الملف بـAST inventory على مستوى class/table، مع اكتشاف `__tablename__` والحقول المباشرة والوراثة من `SoftDeleteMixin` وتصنيف lifecycle. تمت إضافة الجداول المكتشفة إلى `protected_tables_registry.md`، وتصحيح أسماء `lab_subscriptions` و`quality_controls`، وإضافة ADR-026 الذي يمنع schema rollout غير المعتمد.

النتيجة الحالية للـinventory هي 68 model classes، ولا توجد جداول غير مسجلة. توجد 61 business models بلا soft-delete support فعلي؛ لذلك يعيد الوضع الافتراضي `WARNING / exit 1`، بينما يعيد `--ci --strict` `FAIL / exit 2` لحجب release السريري حتى يتم اعتماد وتنفيذ lifecycle وdefault-filter evidence. هذا سلوك مقصود وليس فشلاً مخفياً.

أضيفت ستة اختبارات للـgate، وثلاثة اختبارات لفاحص الأسرار، واختباران للبوابات المنفردة. كما تم تقوية `gula_citizen_portal.py` و`gula_registration_portal.py`: لا توجد demo credentials أو PII في main execution، وأصبح password hashing باستخدام PBKDF2 مع salt عشوائي وformat versioned، مع رفض legacy SHA-256 والمصادقة قبل كتابة سجل طبي.

تم تحسين `.audit/scan_secrets_safe.py` لعدم اعتبار environment references وdocumentation headers أسراراً literal، مع الإبقاء على كشف PEM فعلي. النتيجة: 17 findingاً إجمالاً، 0 non-placeholder findings، و9 test-fixture-like findings. تبقى مراجعة تدوير مفاتيح الإنتاج مسؤولية التشغيل والأمن.

تم إصلاح test collection الخاص بـdevice_bridge: root pytest يشغل `backend/tests` و`tests` فقط، بينما تمت إضافة CI job مستقل للخدمة مع `PYTHONPATH=.:../..`. بعد الإصلاح نجحت اختبارات device_bridge وعددها 30 اختباراً، ونجحت مجموعة root كاملة بعد الفصل بعدد 2732 اختباراً و4 skipped و21 warning. فشل root collection السابق كان بسبب خلط حزم `app` المستقلة، وليس بسبب Rule 10.

## بوابات الجولة الحالية

| البوابة | النتيجة |
|---|---|
| Root full pytest | **2732 passed, 4 skipped, 21 warnings** |
| Device bridge isolated pytest | **30 passed, 1 warning** |
| Rule 10 default | `WARNING / exit 1`، 68 models، 61 gaps حقيقية، 0 unregistered |
| Rule 10 strict | `FAIL / exit 2` كما هو مطلوب قبل اعتماد rollout الإنتاجي |
| Rule 10/security targeted tests | **11 passed** |
| Standalone portal + scanner tests | **5 passed** ضمن المجموعة targeted |
| Python compileall | ناجح للـbackend/shared/services/edge_agent/scripts وملفات الأمن الجديدة |
| Ruff E9/F | ناجح على الملفات المعدلة |
| Secret scanner | 0 non-placeholder findings |
| CI YAML | صحيح، وjob `device-bridge-tests` موجود ومعزول |
