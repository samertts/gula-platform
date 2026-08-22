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
| Backend full suite | **2721 passed, 4 skipped, 21 warnings** خلال 216.12 ثانية. |
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

أُعيد تشغيل `scripts/data_preservation_gate.py` كما هو. النتيجة هي **exit code 1 / WARNING**، وليس PASS. وجد الكاشف 29 نموذج أعمال بلا حقول soft-delete وفق heuristic على مستوى الملف، من بينها نماذج legacy مثل patients وlab_orders وlab_results وsamples وtest_results، إضافة إلى كيانات أخرى. التحليل السابق يبين أن الكاشف الحالي لا يفهم الوراثة والـ mixins ولا يطبق فحص default query filtering، كما يصنف بعض الكيانات التشغيلية أو append-only بطريقة خشنة.

هذا التحذير يتضمن فجوة حقيقية في نماذج أعمال legacy، وليس مجرد خطأ يمكن إخفاؤه. لذلك لم تُضف migration شاملة إلى الجداول المحمية، ولم تُغيّر سياسة CI التي تفرق بين WARNING وFAIL. المعالجة الصحيحة التالية تحتاج سجل protected-table واعياً بالـ AST/class/inheritance، وتصنيف الاستثناءات المسموح بها، ثم Architecture Board approval لإضافة schema وحقول `deleted_at` و`deleted_by` و`is_deleted` وتطبيق filtering افتراضي مع backup وrollback واختبارات عزل المستأجرين.

> الاستنتاج التشغيلي: Data Preservation Gate صالح حالياً كإشارة مراجعة، لكنه لا يثبت اكتمال Rule 10. لا ينبغي اعتبار branch جاهزاً لإغلاق هذا البند قبل اعتماد rollout رسمي.

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

بعد مراجعة هذا التقرير وdiff المراحل، يُدفع الفرع إلى GitHub ويُفتح PR موجّه إلى `main` من دون auto-merge. يجب تقييم CI المنشور مع التمييز بين فشل job فعلي وفشل pre-execution بسبب billing أو Vercel. ولا يُغلق PR أو يُدمج قبل مراجعة WARNING الخاص بـ Rule 10 واعتماد خطة schema مستقلة.
