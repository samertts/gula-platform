# سجل التدقيق والمعالجة المستمرة لمنصة GULA

**التاريخ:** 2026-08-18

## النطاق

يغطي هذا السجل تدقيق توافق Alembic، اختبارات backend، فحوصات إعدادات البنية التحتية، صور الحاويات، وحالة GitHub. نُفذت الفحوصات في بيئة محلية مع إبقاء `SAFE_STOP` فعالاً. لم تُنفذ أي migration على PostgreSQL فعلي، ولم يحدث نشر أو دمج أو حذف فروع.

## النتائج المثبتة

نجح توليد SQL لمسار `alembic upgrade head --sql` باستخدام PostgreSQL dialect بعد معالجة introspection غير المتوافق مع `MockConnection`. كما نجح توليد SQL لمسار `alembic downgrade head:base --sql` بعد اكتشاف وإصلاح أخطاء downgrade إضافية في migrations القديمة، منها استدعاءات `op.drop_column` ناقصة اسم الجدول ومسارات downgrade تعتمد على `Inspector` في offline mode.

| البوابة | النتيجة |
|---|---:|
| Compile للمigrations | ناجح، `rc=0` |
| Alembic upgrade offline | ناجح، `rc=0`، 7,448 سطراً مولداً |
| Alembic downgrade offline | ناجح، `rc=0`، 1,360 سطراً مولداً |
| `git diff --check` | ناجح |
| الاختبارات المستهدفة | 30 ناجحة، 4 متجاوزة لغياب Staging URL |
| اختبارات backend الكاملة | 2,732 ناجحة، 5 متجاوزة، 20 تحذيراً |

## الإصلاحات الإضافية في هذه الدورة

أُضيفت مسارات downgrade offline-safe إلى migrations الخاصة بـworkspace architecture، membership relationship engine، role permission engine، وsecurity audit governance. كما عولجت migrations الأساسية الخاصة بـmulti-rail orchestration، performance indexes/audit protection، وroles hierarchy. التحقق النهائي بعد هذه التعديلات لم يسجل `NoInspectionAvailable` أو `MockConnection` أو `TypeError` أو `AttributeError`.

## العوائق المتبقية

ما زالت ثمانية مراجع صور حاويات GULA في Kustomize base تستخدم `:latest`: backend و`svc-lab` و`svc-patient` و`svc-order` و`svc-result` و`svc-sample` و`svc-notification` و`svc-ai`. لا توجد digests متاحة في المستودع، ورفض GHCR القراءة غير الموثقة بحالة `401`، كما لم تُعثر نسخ الحزم عبر GitHub API. لذلك لم يُستبدل `latest` بتاغ أو digest مخمّن؛ يلزم توفير manifest/digest موثق من CI أو registry قبل تعديلها.

أظهر `security_scan_config.py` ثمانية Findings بدرجة HIGH، وكلها تخص الصور غير المثبتة. وأظهر Architecture Guardian آلاف مخالفات layer-boundary في baseline الحالي؛ لا يجوز اعتبارها إصلاحاً آمناً دفعة واحدة دون تحديد baseline معتمد وتقسيمها إلى PRs صغيرة، لأن بعضها ديون معمارية تاريخية وليست كلها ناتجة عن هذه الدورة.

فحص Dependency Guardian أظهر أولاً 33 تعارضاً نصياً بين manifests الدنيا وملف lock الدقيق. عولجت الأداة نفسها حتى تتحقق من توافق pin صريح `==version` مع جميع القيود بدلاً من مقارنة النصوص، وتسمح exact pins داخل ملف lock دون اعتبارها غياب minimum bound. بعد الإصلاح أصبحت النتيجة `rc=0` مع صفر vulnerabilities، صفر outdated، وصفر conflicts في الفحص المحلي غير الشبكي. كما اجتاز `py_compile` وRuff المحدد لـF401 و`git diff --check`. أضيف اختبار regression مستقل؛ اجتاز 3 اختبارات، واجتاز ملف الاختبار Ruff. أما Ruff الكامل للأداة القديمة فما زال يعرض مخالفات أسلوبية تاريخية لا تتعلق بمنطق التوافق الجديد. أداة `pip-audit` غير متاحة محلياً، لذلك لا يُعد الفحص الأمني للـPython dependencies مكتملاً خارج نتائج الأداة الحالية.

اختبارات schema الحية الموسومة integration تجاوزت بأمان بسبب غياب `MIGRATION_DATABASE_URL`. عند وجود هذا المتغير مع هدف غير متاح، قد تتوقف الاختبارات بلا timeout اتصال واضح؛ يجب جعل الاختبارات الحية تستخدم مهلة اتصال قبل تشغيل Staging.

## قرارات السلامة

لا تُنفذ production migration، ولا تُرسل بيانات NID أو EHR أو دفع حقيقية، ولا تُثبت digests غير معروفة، ولا تُدمج Pull Requests أو تُغير حماية الفروع أثناء `SAFE_STOP`. اختبار offline يثبت قابلية توليد SQL فقط؛ يلزم PostgreSQL Staging للتحقق من idempotency، القيود الأجنبية، الفهارس الموجودة مسبقاً، وترتيب البيانات في schema قائم.

## نتائج الدورة المتقدمة

اكتُشف خلل rendering في Helm: helper `gula.image` يعتمد على `.Values` بينما استدعاءات backend وfrontend كانت تمرر `dict` بلا سياق Values. أُصلح الاستدعاءان بتمرير `Values` صراحة. وأضيف حارس fail-closed إلى helper بحيث يرفض rendering عندما تكون البيئة production وtag الصورة `latest`، مع طلب tag immutable أو digest موثق. وأضيف الحارس نفسه إلى قالب microservices قبل إنشاء الخدمات الثمانية، بحيث لا يمر global `imageTag=latest` في rendering إنتاجي. تعذر تشغيل Helm نفسه محلياً لأن binary غير متاح، كما تعذر تنزيله ضمن المهلة الشبكية؛ لذلك ثبت الإصلاح ساكنًا بفحص جميع المستدعين ونجح فحص `git diff --check`، لكنه ما زال يحتاج `helm template` أو `helm lint` في CI.

أضيفت مهلة PostgreSQL قابلة للضبط إلى اختبارات schema الحية الأربع عبر `MIGRATION_DB_CONNECT_TIMEOUT` وبقيمة افتراضية خمس ثوانٍ. اجتازت هذه الملفات Ruff، وأُعيد تشغيل الاختبارات مع غياب عناوين Staging فكانت النتيجة أربع حالات skipped صريحة بدلاً من تعليق. ما زال إثبات الاتصال الحقيقي والـschema يتطلب PostgreSQL Staging.

قُوّي `scripts/generate-sbom.sh` ليعمل fail-closed: لم يعد يضع `backend:latest` كقيمة افتراضية، ويرفض تشغيل SBOM للحاويات إذا لم تُمرر `CONTAINER_IMAGE` أو إذا كانت الإشارة تنتهي بـ`latest`. كما أصبح `syft` مطلوباً فقط في all/container modes؛ يعمل Python mode مع fallback الموجود دون syft، بينما يرفض container mode بوضوح عند غياب syft. اجتاز الملف `bash -n`، ونُظفت artifacts التجريبية بعد الاختبار.

قُوّيت workflows الخاصة بـblue-green وcanary بحيث ترفض image tag فارغاً أو `latest` أو `latest-*` أو tag غير مطابق للنمط المسموح قبل تنفيذ `kubectl`. اجتاز YAML parsing للملفين، وأثبت اختبار shell أن `abc1234` مقبول وأن `latest` و`latest-region-me` والقيمة الفارغة مرفوضة. كما اكتُشف أن blue-green يتوقع workflow باسم `CI - Build, Test & Security Scan` بينما كان CI يحمل اسماً مختلفاً؛ عُدّل الاسم ليعمل `workflow_run` trigger، ثم اكتُشف reference ثانٍ في opt-in auto-merge كان يشير إلى الاسم القديم؛ عُدّل أيضاً إلى الاسم الجديد مع بقاء الدمج opt-in. ثبتت صحة YAML للـCI والـblue-green والـcanary والـopt-in auto-merge. هذا يمنع النشر غير المثبت، لكنه لا يوفر digest للخدمات الثمانية داخل Kustomize base؛ يبقى مصدر digest الموثق مطلوباً.

| الفحص الجديد | النتيجة |
|---|---:|
| Static check لاستدعاءات `gula.image` | لا توجد استدعاءات بلا `Values` |
| security scanner على مجلد Helm | 0 Findings |
| بوابة التحقق الأخيرة | 33 اختباراً ناجحاً، YAML workflow ناجح، `git diff --check` ناجح |
| اختبارات schema الأربعة مع غياب Staging | 4 skipped، `rc=0` |
| staging_preflight ببيئة اصطناعية متسقة | PASS، دون external calls |
| Ruff للملفات الأربعة | ناجح، `rc=0` |
| Helm lint/template | غير منفذ؛ Helm غير متاح محلياً |
| phase4 compile/shell/YAML/diff gates | كلها ناجحة؛ security scanner ما زال يحجب بسبب 8 HIGH للصور |

## الخطوات التالية

الخطوة الآمنة التالية هي الحصول على قائمة digests من pipeline أو registry الموثق، ثم إدخالها في Kustomize وHelm عبر PR منفصل مع فحص `security_scan_config.py`. بعدها يجب تجهيز PostgreSQL وRedis و`AUDIT_ANCHOR_DIR` منفصلة لـStaging، تشغيل migrations online على نسخة غير إنتاجية، وإعادة اختبارات schema الحية بمهلات اتصال ومراقبة rollback.
