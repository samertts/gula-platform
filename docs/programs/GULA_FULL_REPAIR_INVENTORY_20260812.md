# GULA Full Repair Inventory — 2026-08-12

## Scope and safety boundary

هذا الجرد يهدف إلى تحويل طلب الإصلاح الشامل إلى موجات قابلة للقياس. لا يعني الجرد أن المنصة صالحة للإنتاج الوطني، ولا يخول حذف الفروع أو إعادة تسميتها أو نقل deployment أو إنشاء release. تبقى Wave 3 وCitizen C1/C2 هي خط الأساس المعتمد.

## Confirmed high-priority findings

| المجال | الدليل الحالي | الخطر | الموجة |
|---|---|---|---|
| Web/platform auth | عدة تطبيقات تحت `platform/apps/` تقرأ وتكتب access/refresh tokens في `localStorage` | XSS أو browser extension قد يسرق credentials طويلة العمر | R1: cookie-only session migration |
| Laboratory offline replay | laboratory API يخزن auth headers في offline queue ويعيد تشغيلها لاحقاً | بقاء bearer token في IndexedDB/queue، وإعادة طلب قديم بلا session validation | R1/R2: queue redaction + session-bound replay |
| Ministry shell | ProtectedLayout يعتمد على localStorage token، وLogin يكتب `mock-jwt-token` | mock authentication قد يبدو كدخول حقيقي ويفصل UI عن backend authorization | R1: backend session bootstrap or explicit Demo-only gate |
| Canonical/legacy duplication | `frontend-v3`, `platform/apps/*`, و`apps/gula-web-suite` surfaces متعددة | اختلاف عقود auth والبيانات وعدم وضوح source of truth | R3: route/API inventory قبل أي freeze/rename |
| Default branch dependencies | GitHub ما زال يعرض 133 Dependabot alerts في default branch | المخاطر لا تختفي بمجرد إصلاح branch review | R4: merge decision/PR after approval |
| Operational claims | وجود Docker/Terraform/Helm/CI لا يثبت backup restore أو production readiness | احتمال إعلان جاهزية دون evidence | O1/I1/O2 gates |

## Existing verified controls

ثبتت Wave 3/C1/C2 ضوابط mapping القابل للعكس، server-side relationship authorization، own-context citizen routes، idempotency، audit، migrations قابلة للعكس، وbackend regression suites. لا يوجد backfill أو dual-write أو automatic matching.

## Repair order

تبدأ الدفعة الأولى بإزالة تخزين access/refresh tokens من browser storage في التطبيقات التي تستخدم cookie-compatible backend، مع إبقاء user display metadata غير الحساسة فقط عند الحاجة. يجب أن تشمل الدفعة normal fetch وrefresh وXHR upload وoffline queue؛ إصلاح fetch وحده غير كافٍ.

بعد ذلك تُنفذ بوابات logout/session bootstrap والـDemo isolation، ثم تُراجع IndexedDB caches والـoffline writes وidempotency/conflict handling. بعدها فقط تُستكمل dependency/build/CI and integration gates. لا تُعالج المشاكل بإخفاء الاختبارات أو تعطيل validation أو إضافة wildcard authorization.

## Evidence required for each repair wave

كل موجة يجب أن تقدم diff محدوداً، اختباراً سلبياً، build/typecheck إن كان frontend، ونتيجة Backend/contract suite ذات صلة. أي claim عن backup أو availability أو protocol interoperability يحتاج تشغيل فعلياً في بيئة معزولة، وليس وجود ملف configuration فقط.

## Current exclusions

الملفان `.audit/ci-fix.patch` و`.audit/ci-repair.patch` غير متتبعين ومحافظ عليهما خارج commits. لا تشمل هذه الموجة حذفهما، ولا branch pruning، ولا frontend-v3 rename، ولا GitHub Release، ولا production deployment changes.

## R1 execution evidence — 2026-08-12

تم تنفيذ ترحيل cookie-only على citizen وlaboratory وdoctor وhospital وnurse وpharmacy وradiology وministry. أزيلت مراجع token/refresh من `localStorage` وAuthorization headers من browser clients، وأضيفت `credentials: include` إلى fetch و`withCredentials` إلى XHR upload حيث ينطبق ذلك. نُقحت offline queue headers بحيث لا تُخزّن أو تعيد تشغيل Authorization headers. أصبح Ministry shell يعتمد على `/auth/session`، بينما أصبح مسار العرض التجريبي بوابة صريحة لا تُفعل إلا مع `VITE_DEMO_MODE=true` وsessionStorage gate، وتمنع اتصالات `/ministry/*` الحية أثناء Demo.

| الفحص | النتيجة | الدليل/الحد |
|---|---|---|
| Backend full suite | **2305 passed** | `/tmp/gula_r1_backend.log`، 251 warnings، 267.82s |
| Direct TypeScript check للملفات المعدلة مع Vite typings وTypeScript 5.9.3 | **12/12 passed** | سجلات `/tmp/gula_r1_file_vite_*` |
| Vite bundling | citizen وlaboratory وdoctor وhospital وpharmacy: **passed** | سجلات `/tmp/gula_r1_*_vite2.log` |
| Vite bundling المتبقي | nurse: blocker بسبب missing default exports في صفحات قائمة مسبقاً؛ ministry: missing service exports؛ radiology: مراجع `src/styles/theme.css` و`components.css` غير موجودة | لم تُخفَ هذه النتائج ولم تُحوّل إلى نجاح مصطنع |
| token scan | **NO_TOKEN_AUTH_OCCURRENCES** | لا توجد نتائج في `platform/apps` لـlocalStorage token/refresh أو Authorization Bearer أو mock-jwt |

تظل هذه الموجة غير كافية لإعلان readiness إنتاجية وطنية. ما زالت إصلاحات R2 الخاصة بتنظيف بيانات offline queue القديمة، وR3 الخاصة بجرد الواجهات والعقود، وR4 الخاصة بقرار دمج Dependabot والفرع الافتراضي خارج هذه الدفعة. كما لا تشمل هذه الموجة أي حذف للفروع أو rename أو release أو تغيير deployment.

### Build-tool compatibility note

أمر `npm run build` الأصلي يستخدم TypeScript 7.0.2 في التطبيقات، بينما تحتوي project configs الحالية على خيارات legacy مثل `baseUrl` و`allowImportingTsExtensions` وعلى project reference غير composite لـ`platform/ui`. لذلك فشلت هذه الأوامر قبل الوصول إلى كود R1. تم فصل ذلك عن التحقق المباشر باستخدام TypeScript 5.9.3 وعن Vite bundling، ولم تُعدّل إعدادات TypeScript العامة ضمن R1 حتى لا تتسع الموجة دون اعتماد.
