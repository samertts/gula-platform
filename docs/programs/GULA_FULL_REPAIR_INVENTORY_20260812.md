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

## R2 status — 2026-08-12

اكتملت دفعة R2 على مستوى المصدر: cleanup/migration للـIndexedDB request queues، queue rejection metadata، sanitizer مشترك، purge لقاعدة Workbox Background Sync، وإزالة worker mutation replay القديم. تم الحفاظ على drafts وcache وclinical stores؛ لا توجد عملية `deleteDatabase` عامة لتلك المخازن.

الأدلة: اختبار sanitizer ناجح، helper TypeScript ناجح، Vite build ناجح في citizen/doctor/hospital/laboratory/pharmacy، وBackend suite بنتيجة **2305 passed**. Nurse وMinistry وRadiology لا يمرون build كاملاً بسبب blockers سابقة موثقة: صفحات Nurse بلا default exports، Ministry services بلا exports مطلوبة، وRadiology CSS imports غير موجودة. فشل TypeScript project checks سببه إعدادات TypeScript 7/legacy project references، ولم تُعدّل ضمن R2.

تبقى `queue_rejections` محلية metadata فقط ولا تحفظ قيمة token. أي مستخدم لم يفتح نسخة التطبيق الجديدة قد يحتفظ ببيانات قديمة في متصفحه إلى حين startup/activation التالي؛ لا يمكن للمستودع تنظيف متصفح غير متصل أو غير محدث عن بُعد.


## R3 status — 2026-08-12

تم تنفيذ عقد queue مشترك في `platform/ui/utils/offlineQueueContract.ts` وربطه بمسارات Citizen وDoctor وLaboratory وNurse وPharmacy. يشمل العقد `operationId` و`idempotencyKey` و`requestFingerprint` و`expectedVersion` وحالات `pending/synced/conflict/rejected/failed`، ويمنع حذف أو replay تلقائي عند `409/412`. أضيف backend compare-and-set لـ`LabOrder.version` على validation عبر `If-Match`، مع اختبار يثبت أن الإصدار القديم يُرفض بـ409 دون تغيير أو قفل صامت.

تم إصلاح أخطاء build المثبتة في Nurse وMinistry وRadiology: توحيد default exports في صفحات Nurse، إضافة facades typed لخدمات Ministry فوق API الحقيقي، إزالة imports غير المثبتة لـ`motion/react`، وتصحيح مسارات CSS في Radiology. الأدلة الحالية: **8/8 Vite builds ناجحة** للتطبيقات المتأثرة، **2306 اختبار Backend ناجح**، اختبارات contract/security ناجحة، و`git diff --check` ناجح. يظل دعم idempotency/version backend غير معمم على كل endpoint سريري، ولذلك لا تعلن R3 readiness إنتاجية وطنية ولا تشمل deployment أو Wave 4 أو Dependabot merge.


## Directive execution — error contract hardening — 2026-08-12

تم تحويل القسم 28 من directive إلى إصلاح محدود في طبقة FastAPI المركزية دون تغيير مسارات الأعمال أو المصادقة أو deployment. أضيف `backend/app/core/error_contract.py` لبناء الاستجابة القياسية `code/message/details/request_id/timestamp` مع إبقاء `detail/detail_ar` للتوافق الخلفي. سُجلت handlers لـ`DomainError` و`StarletteHTTPException` و`RequestValidationError` والاستثناءات غير المعالجة، بما في ذلك route-not-found وvalidation failures.

يمنع العقد إعادة قيم Pydantic الحساسة مثل `input` و`ctx`، ويمنع إعادة سبب readiness الداخلي أو traceback أو تفاصيل بنية البيانات في استجابات العميل. كما ثُبت التفريق التشغيلي بين `401` للمصادقة المطلوبة و`403` لفشل التفويض، مع رموز مستقرة للتعارض و`If-Match` وفشل rate limit.

| الفحص | النتيجة |
|---|---|
| Error contract unit tests | **4 passed** |
| Resilience + Demo security + error contract | **29 passed** |
| Backend full suite بعد آخر تعديل | **2310 passed، 251 warnings** خلال 249.89 ثانية |
| Python compile check | **passed** |
| `git diff --check` قبل التوثيق | **passed** |

### حدود directive التي لم تُنفذ تلقائياً

كشف تدقيق base URLs وجود اختلافات موثقة بين `api.gulaplatform.com` و`api.gula-platform.com` و`api.gula.iq`، إضافة إلى إعدادات staging مختلفة. لم تُعدّل هذه القيم لأن توحيدها يغير deployment/production behavior ويحتاج environment strategy وADR وChange Control واختبار mobile/edge فعلياً. كذلك لم تُنفذ إعادة بناء Workspaces أو محركات المواعيد والصفوف أو تكامل FHIR/HL7/DICOM أو تعميم If-Match/idempotency على كل endpoint، لأن ذلك يتطلب موجات مستقلة وتحليلاً endpoint-by-endpoint، ولم تُنفذ أي عملية Wave 4 أو Dependabot merge أو branch operation.


## Directive verification — frontend build boundary — 2026-08-12

أُجريت محاولة build فعلية للتطبيقات الثمانية. أمر `pnpm run build` لم يصل إلى TypeScript أو Vite لأن workspace tooling أوقف `pnpm install` تلقائياً عند `ERR_PNPM_IGNORED_BUILDS` لـ`esbuild@0.28.2`. لم تتم الموافقة على build scripts ولم يُعدّل lockfile أو إعدادات supply-chain؛ أزيلت artifacts الآلية بعد التحقق من أنها غير متتبعة.

للفصل بين مشكلة tooling ومشكلة bundling، شُغّل Vite المحلي مباشرة دون تشغيل install أو تعديل configuration، وكانت النتيجة **8/8 Vite bundling ناجحة**: citizen، doctor، hospital، laboratory، ministry، nurse، pharmacy، radiology. أما direct `tsc -b` فبقي محجوباً بإعدادات TypeScript 7/legacy الحالية (`allowImportingTsExtensions`، `baseUrl`، ومرجع `platform/ui` غير composite)، وهي حدود موثقة من R3 ولم تُعدّل ضمن هذه الموجة.


## Source-mode and script-chain verification — 2026-08-12

اكتملت دفعة إصلاح Source-mode على الفرع `fix/typescript-source-mode-20260812` دون تغيير Wave 3 أو سلوك deployment. أضيف `typecheck: tsc --noEmit` إلى `platform/ui` وإلى التطبيقات الثمانية، ووُحّد أمر build في كل تطبيق إلى `npm run typecheck && vite build`. لم يُعدّل `pnpm-workspace.yaml` أو أي lockfile التزاماً بحدود هذه الدفعة؛ لذلك لا يُدّعى أن workspace package discovery قد أُعيد تصميمه.

| الفحص الفعلي | النتيجة | الحدود والدليل |
|---|---:|---|
| `npm run typecheck` عبر UI + التطبيقات الثمانية | **9/9 ناجح، 0 أخطاء TypeScript** | شُغّل لكل manifest مستقل باستخدام local TypeScript 7.0.2 |
| فحص `tsconfig.node.json` في Pharmacy وRadiology | **2/2 ناجح** | فحص إضافي مستقل لـVite config types |
| `npm run build` للتطبيقات الثمانية | **8/8 ناجح** | شمل typecheck الموحد ثم Vite bundling؛ لا deployment أو release |
| Backend `pytest -q --tb=short` | **2310 passed، 251 warnings** | 252.12 ثانية؛ التحذيرات Deprecation/SQLAlchemy موثقة ولم تُخفَ |
| `git diff --check` | **ناجح** | لا whitespace errors |
| diff secret-pattern scan | **لا نتائج** | الفحص اقتصر على التغييرات غير المستثناة ولم يقرأ أو يطبع أسراراً |
| `npm audit --json` على root lockfile | **0 advisories في هذه البيئة** | قراءة فقط؛ لم يُنفذ `npm audit fix` ولم يُعدّل lockfile |

لا تزال ملاحظات GitHub Dependabot البالغ عددها 133 على الفرع الافتراضي خارج هذه الدفعة، ولا يجوز اعتبار نتيجة audit المحلية قراراً بدمجها أو إغلاقها. كما بقي الملفان `.audit/ci-fix.patch` و`.audit/ci-repair.patch` خارج أي commit، ولم تُنفذ branch pruning أو rename أو release أو merge إلى `main`.

## Remaining safety boundary after TypeScript repair

هذه الدفعة تثبت صحة typecheck ومسار bundling الحاليين، ولا تثبت وحدها جاهزية تشغيل وطنية أو سلامة تكاملات Web/Android/Windows أو Demo isolation في بيئة production. ما زالت اختبارات التشغيل الفعلي، مصفوفة endpoints الشاملة لـRBAC وIf-Match/idempotency، اختبار الاستعادة والنسخ الاحتياطي، وتوحيد بيئات base URL تحتاج موجات مستقلة واعتماداً صريحاً. لم تُستخدم إصلاحات TypeScript لتجاوز validation أو audit أو authorization، ولم تُضف صلاحيات wildcard أو تخزين رموز في browser storage.


## Frontend–Backend Integration and UX Follow-up — 2026-08-12

تم تنفيذ دفعة تكامل أمامية/خلفية على فرع `feat/frontend-backend-ux-20260812` دون تعديل `main` أو سلوك النشر. اعتمدت التطبيقات على عميل Backend مشترك في `platform/ui/services/apiClient.ts` يرسل جلسات HttpOnly، ويدعم عقد الأخطاء القياسي، وrequest metadata، و`If-Match` وidempotency metadata، وإعادة المحاولة الآمنة لطلبات القراءة فقط. كما تم تصحيح توجيه Demo بحيث تُرسل الطلبات إلى `VITE_DEMO_API_BASE_URL` المعزول فعلياً، مع رفض صريح عند غياب عنوان Demo أو محاولة الوصول إلى أصل الإنتاج.

| المجال | ما نُفّذ | الدليل |
|---|---|---|
| UI platform | إضافة `createApiClient` و`useBackendResource` وتعريفات Vite وتصديرها من الحزمة المشتركة | `platform/ui/services/`, `platform/ui/hooks/`, `platform/ui/index.ts` |
| Citizen | ربط Home بـ`/citizen-platform/me/dashboard` مع loading/stale/error/retry، وربط HealthAssistant بـ`POST /ai/fabric/chat` بدلاً من الردود المحلية الوهمية | `platform/apps/citizen/src/pages/Home.tsx`, `HealthAssistant.tsx`, `services/guideAssistant.ts` |
| التطبيقات السريرية | توحيد العملاء في Doctor وHospital وLaboratory وMinistry وNurse وPharmacy وRadiology مع الحفاظ على عقود الواجهات وoffline queue حيث كانت موجودة | ملفات `services/api.ts` لكل تطبيق |
| Nurse | استبدال fixtures في TaskList وShiftHandover بخدمات `/nursing/tasks` و`/nursing/handover` مع mappers typed وحالات empty/error/retry/create | `platform/apps/nurse/src/services/tasks.ts`, `handovers.ts`, `TaskList.tsx`, `ShiftHandover.tsx` |
| تجربة المستخدم | skeleton/feedback/error retry، إبقاء البيانات السابقة أثناء refetch، ومنع تكرار رسالة المستخدم عند إعادة محاولة المساعد | `useBackendResource.ts`, `Home.tsx`, `HealthAssistant.tsx` |

تم التحقق الفعلي من بوابات TypeScript: **9/9 مشاريع ناجحة بصفر أخطاء**. كما نجحت builds للتطبيقات الثمانية: Citizen وDoctor وHospital وLaboratory وMinistry وNurse وPharmacy وRadiology. ظهرت تحذيرات Vite الحالية المتعلقة باستخدام `__dirname` مع `configLoader: native` في بعض التطبيقات؛ لم تُعدّل لأنها خارج نطاق التكامل ولا تمنع البناء.

أعيد تشغيل اختبارات Backend الكاملة بعد التغييرات: **2310 اختباراً ناجحاً و251 تحذيراً خلال 287.45 ثانية**. التحذيرات تشمل deprecation warnings معروفة وSecurityWarning في fixture اختبار توقيع، ولا تمثل فشلاً في هذه الدفعة.

### حدود الدفعة

هذه الدفعة لا تعني أن كل صفحة في التطبيقات الثمانية أصبحت خالية من fixtures؛ ما زالت بعض شاشات Hospital وDoctor وNurse وRadiology تحتوي بيانات عرض تجريبية أو وظائف محلية، وسيتم تحويلها في موجات منفصلة بعد مطابقة كل شاشة مع endpoint فعلي وصلاحياته. كما أن Guide Assistant مرتبط بعقد AI Fabric الموجود، لكنه لا يقدّم تشخيصاً أو قراراً علاجياً ويظل خاضعاً للتنبيه التوعوي في الواجهة.

لم تُعدّل lockfiles أو `.audit/ci-fix.patch` أو `.audit/ci-repair.patch`، ولم تُعالج تنبيهات Dependabot، ولم يُنفّذ merge أو release أو branch pruning. نجاح typecheck/build والاختبارات لا يثبت وحده جاهزية إنتاج وطنية؛ يلزم قبل الإنتاج اختبار عقد API في بيئة Demo معزولة، واختبار RBAC ومسارات 401/403/409/412، واختبارات تشغيل واستعادة وقياس أداء تحت الحمل.
