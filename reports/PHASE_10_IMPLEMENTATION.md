# تقرير تنفيذ IAM Phase 10 — Frontend/Backend/Mobile Contract Parity

**المشروع:** GULA Platform
**المستودع:** `samertts/gula-platform`
**الفرع الأساسي للعمل:** `feat/iam-phase9-security-audit`
**التاريخ:** 2026-08-14
**الحالة:** دفعة Phase 10 أولى مكتملة محليًا؛ functional parity الكامل لم يُعلن لأن عقود القراءة السريرية القديمة لا تزال غير NIAM/workspace-enforced.

## الملخص التنفيذي

تم تنفيذ تدقيق مصدرّي لـPhase 10 بدل افتراض أن وجود شاشة أو route أو TypeScript type يعني أنها متصلة تشغيليًا. أُنشئت جردات فعلية للتطبيقات والمسارات وواجهات FastAPI المركبة ومصفوفة Frontend/Backend، ثم تم تدقيق عقود المرضى والطلبات والنتائج والعينات وواجهات NIAM والـlegacy bridges.

النتيجة الأساسية هي أن frontend-v3 يملك مسارات كثيرة، لكن عدة أسطح سريرية محجوبة عمدًا لأن backend الحالي يعتمد `LabUser` و`lab_id` القديمين، وليس `NiamActor` وسياق workspace/facility/organization المطلوب. لم تتم إزالة الحاجز ولم يتم تشغيل fallback إلى frontend-v2 أو mock data؛ بدل ذلك وُثقت الفجوة كـ`BLOCKED_SAFE` و`DECISION_REQUIRED`.

> **قاعدة هذه الدفعة:** عدم إثبات سلسلة frontend → auth → authorization → real API → service → database → response يعني عدم إعلان الشاشة مكتملة.

## الجرد الفعلي

| الأثر | النتيجة |
|---|---:|
| frontend-v3 route entries | **83** بعد إضافة مساري legal العامين |
| frontend-v2 route entries | **34** legacy entries |
| mounted FastAPI routes | **2017** |
| backend snapshot routes في contract audit | **309** |
| frontend data-source surfaces | **88** |
| application surfaces | **14** |
| frontend/backend matrix rows | **83** |

تم توليد الجرد من المصدر الفعلي عبر `scripts/phase10_inventory.py`، وتم استخراج المسارات المركبة من التطبيق عبر `scripts/phase10_fastapi_surface.py`. القيم `UNVERIFIED` لا تعني نجاحًا أو فشلًا؛ تعني أن التحليل السطحي لا يكفي لإثبات العقد وتحتاج إلى تحقق يدوي أو اختبار تكاملي.

## الإصلاحات المنفذة

| المجال | التغيير | النتيجة |
|---|---|---|
| Live capability UX | إضافة `hasReflectedPermission` واستخدامه في `usePermissions` و`Sidebar` | أصبح empty/missing server reflection **deny** بدل fail-open الظاهري؛ backend بقي نقطة enforcement الوحيدة |
| Capability tests | إضافة أربع حالات اختبار للفراغ، السماح المنعكس، الرفض، والقائمة الفارغة | العقد مثبت في Vitest |
| Legal pages | إضافة `/privacy-policy` و`/terms-of-service` في frontend-v3 مع lazy routes، responsive accessible layout، وروابط من AuthLayout | الصفحات قابلة للوصول المباشر وrefresh-safe؛ النصوص معلّمة صراحة بأنها مسودة تحتاج `LEGAL_REVIEW_REQUIRED` |
| Internationalization | إضافة مفاتيح legal بالعربية والإنجليزية؛ بقية اللغات تستخدم fallback المعلن إلى الإنجليزية | لا توجد دعوى دعم لغوي غير مثبت؛ LocaleContext الحالي يضبط `lang` و`dir` |
| Audit verifier | استبدال العدد الخلفي hard-coded `306` بحد أدنى 306 يسمح بإضافات موثقة دون إسقاط الحماية من نقصان routes | `verify:audit-artifacts` عاد ناجحًا مع 309 backend routes و83 frontend entries |
| Data-source governance | تصنيف LegalPage كـ`contract-bound/static` بدل `unbound/non-operational` | inventory أكثر دقة دون إعلان مصدر بيانات تشغيلي |
| Safe bridges | الإبقاء على `DIRECT_REST_SCOPED_READS_BLOCKED = true` لعقدي patients/orders، وعدم تشغيل legacy endpoints مباشرة | لا يوجد تجاوز لسياق NIAM أو fake clinical data |

## التحقق من العقود والسياق

| السطح | الدليل الفعلي | التصنيف |
|---|---|---|
| `/patients` | frontend-v3 يطلب `patients.read` وworkspace context، بينما backend route يعتمد `get_current_user` و`lab_id` | `BLOCKED_SAFE` |
| `/orders` | frontend-v3 يطلب `orders.read`، بينما توجد base/LIMS order surfaces legacy تعتمد `LabUser` و`lab_id` | `BLOCKED_SAFE` |
| `/test-results/*` | backend موجود ومصادق legacy، لكن لا يوجد عقد NIAM/workspace/professional context مثبت للواجهة الموحدة | `LEGACY_BRIDGE` |
| `/samples/*` | backend sample API موجود ومصادق legacy، والصفحة الموحدة bridge-only | `LEGACY_BRIDGE` |
| `/qc` | QCPage direct REST surface؛ client read barrier يمنع القراءة غير المصنفة، والصفحة تعرض loading/error/empty بدل fake success | `PARTIAL/UNBOUND` |
| `/niam/audit` و`/niam/consents` و`/niam/security/incidents` | mounted FastAPI routes تستخدم `get_current_niam_actor` | `CONNECTED backend; frontend mapping pending` |
| `/niam/workspaces/{id}/switch` | مسار server-authoritative موجود | `CONNECTED contract candidate; E2E pending` |

## الفجوات المتبقية والإجراءات المطلوبة

لا تزال functional parity الكاملة غير مكتملة، وهذا مقصود وآمن. أولوية P0 التالية هي تصميم وتنفيذ gateway خادمي versioned/idempotent لقراءات المرضى والطلبات فوق الخدمات الموجودة، بحيث يشتق actor/workspace/facility من الجلسة، يستدعي `AuthorizationDecisionService`، يطبق query-level tenant/resource scope، ويسجل canonical audit. لا يجوز تفعيل القراءة عبر `/authz/check` في المتصفح فقط أو عبر `/orders` و`/patients` legacy مباشرة.

وتبقى mobile Android/iOS/Flutter parity غير مؤكدة لأن toolchains اللازمة غير متاحة محليًا. يجب أن يُثبت CI auth/membership/role/permission/workspace parity قبل إعلان اكتمالها. كما أن تطبيق `gula-web-suite` لديه Router وlocale/auth flow منفصلان، ولذلك صُنّف في application inventory كسطح يحتاج توحيدًا أو bridge موثقًا، لا كجزء متصل تلقائيًا بـfrontend-v3.

لا توجد في هذه الدفعة أي دعوى PACS/DICOM أو HL7/ASTM أو Ministry/government integration. ولا توجد قيم retention أو RPO/RTO مخترعة، ولا يُعتبر legal page مسودةً سياسة قانونية نهائية.

## بوابات الجودة المحلية

| البوابة | النتيجة |
|---|---|
| Backend identity regression غير التكاملية | **162 passed, 3 deselected** |
| Frontend-v3 typecheck | **PASS** |
| Frontend-v3 tests | **38 passed / 11 files** |
| Frontend governance scripts | **PASS**: unification, contracts, integration boundary, data sources |
| Contract audit artifacts | **PASS**: 309 backend routes, 83 frontend entries, 7 domains |
| Frontend production build/PWA | **PASS** |
| Mounted FastAPI audit | **PASS**: 2017 mounted routes emitted |
| Flutter/Android/iOS | **UNVERIFIED locally**؛ toolchain/CI required |

## الملفات المضافة أو المعدلة

| الملف | الغرض |
|---|---|
| `reports/PHASE_10_APPLICATION_INVENTORY.md` | جرد التطبيقات والأسطح |
| `reports/PHASE_10_ROUTE_INVENTORY.md` | جرد frontend-v3/v2 routes |
| `reports/PHASE_10_BACKEND_ENDPOINT_INVENTORY.md` | جرد FastAPI decorators |
| `reports/PHASE_10_FASTAPI_MOUNTED_SURFACES.json` | evidence للمسارات المركبة فعليًا |
| `reports/PHASE_10_FRONTEND_BACKEND_MATRIX.md` | مصفوفة أولية للربط والحالة |
| `reports/PHASE_10_CONTRACT_VALIDATION.md` | تحليل العقود الأساسية والفجوات |
| `reports/PHASE_10_FOUNDATION_REVALIDATION.md` | إعادة تحقق Phases 0–9 من المصدر |
| `frontend-v3/src/permissions/liveCapabilities.ts` | helper server-reflected capability fail-closed |
| `frontend-v3/src/permissions/liveCapabilities.test.ts` | اختبارات capability contract |
| `frontend-v3/src/pages/legal/LegalPage.tsx` | صفحات privacy/terms العامة |
| `scripts/phase10_inventory.py` | مولد الجرد والمصفوفة |
| `scripts/phase10_fastapi_surface.py` | استخراج mounted FastAPI routes |
| `scripts/contract-audit/verify-audit-artifacts.mjs` | verifier يسمح بإضافات موثقة ويحمي الحد الأدنى |

## حالة PR وVercel

أُنشئ [PR #174](https://github.com/samertts/gula-platform/pull/174) من `feat/iam-phase10-contract-parity` إلى `feat/iam-phase9-security-audit`. نجحت بوابات Backend identity وPostgreSQL migration وFrontend-v3 contract/type/build وSecurity/Tenant isolation وVercel Preview Comments. فشل deployment preview في Vercel بحالة `Error` بعد نحو 40 ثانية، ولم يعرض تبويب Runtime Logs سببًا مقروءًا؛ لذلك لم يُخترع سبب ولم تُنفذ إعادة نشر أو عملية تغيير. سُجلت النتيجة في `reports/PHASE_10_VERCEL_FINDINGS.md`.

## قرار هذه الدفعة

هذه الدفعة **جاهزة للمراجعة والرفع** باعتبارها Phase 10 foundation/contract-parity hardening، وليست إغلاقًا نهائيًا لكل فجوات الوظائف. الإصلاحات الفعلية التي تم تنفيذها هي fail-closed live capability UX، legal routes عامة معلّمة بمراجعة قانونية، وتحسين الأدوات والجرد. أما clinical gateway للمرضى والطلبات والنتائج والعينات فهو contract requirement صريح يحتاج قرارًا وتنفيذًا خادميًا منفصلًا، ولا يجوز اختصاره بجسر غير آمن.
