# Phase 10 — التحقق من عقود Frontend/Backend والمصادقة والسياق

## النطاق والمنهج

تمت مقارنة route registry في `frontend-v3/src/routes/index.tsx`، وعمليات API في `frontend-v3/src/api/endpoints.ts` و`workspaceScopedReads.ts`، مع المسارات المركبة فعليًا من `app.main.app.routes`. وجود route أو TypeScript type لم يُعتبر دليلًا على functional parity؛ الدليل المطلوب هو سلسلة: frontend action → authentication → backend authorization → service → real source → response → UI state.

تم تشغيل mounted FastAPI audit فوجد **2017 مسارًا مركبًا**، كما وجد أن مسارات المرضى والطلبات والعينات القديمة تستخدم `get_current_user` و`LabUser.lab_id`. هذا يثبت وجود مصادقة legacy وعزل مختبر تقني، لكنه لا يثبت عقد NIAM/workspace/facility المطلوب لـfrontend-v3.

## العقود التشغيلية الأساسية

| السطح | Frontend source | Backend source الفعلي | المصادقة | سياق النطاق | النتيجة |
|---|---|---|---|---|---|
| Login/session | `authApi.login/session` | `/login` و`/session` في `app/routes/login.py` | cookie/session | هوية الجلسة | **CONNECTED جزئيًا**؛ يحتاج اختبار refresh/revocation end-to-end |
| Patient read | `workspaceScopedReads.listPatients` | `/patients` في `app/routes/patients.py` | `get_current_user` | `lab_id` فقط | **BLOCKED_SAFE**؛ لا يجوز تمرير legacy LabUser كبديل NIAM workspace |
| Orders read | `workspaceScopedReads.listOrders` | `/orders` في `app/routes/results.py`، مع surface LIMS منفصل | `get_current_user` | `lab_id` فقط | **BLOCKED_SAFE**؛ توجد duplicate/legacy order surfaces ولا يوجد عقد NIAM مثبت لـv3 |
| Test results | `ResultsPage`/legacy bridge | `/test-results/*` في `app/routes/test_results.py` | `get_current_user` | `lab_id` وrole legacy | **LEGACY_BRIDGE**؛ لا expose سريري قبل عقد facility/workspace/professional context |
| Samples | `SamplesPage`/legacy bridge | `/samples/*` في `app/routes/samples.py` | `get_current_user` | `lab_id` | **LEGACY_BRIDGE**؛ backend موجود لكن contract parity غير مثبت |
| QC | `QCPage` → `qcApi.list` | `/qc` في `app/routes/quality_control.py` | `get_current_user` | legacy lab scope | **PARTIAL/UNBOUND**؛ client read barrier يمنع التشغيل غير المصنف، والصفحة تعرض error state بدل fake success |
| NIAM audit | governance pages/API | `/niam/audit` في `app/identity/api/audit.py` | `get_current_niam_actor` | organization/workspace عبر authorization | **CONNECTED backend**؛ UI action mapping يحتاج permission-level verification |
| NIAM consent | consent page/API | `/niam/consents` في `app/identity/api/consents.py` | `get_current_niam_actor` | subject/grantee and policy | **CONNECTED backend / frontend pending** |
| NIAM incidents | security page/API | `/niam/security/incidents` في `app/identity/api/security.py` | `get_current_niam_actor` | organization | **CONNECTED backend / frontend pending** |
| Workspace switch | `apiClient.switchWorkspace` | `/niam/workspaces/{id}/switch` | `get_current_niam_actor` | server-authoritative context | **CONNECTED contract candidate**؛ يحتاج E2E session/context assertion |

## سبب الإبقاء على الحاجز

يُعرّف `workspaceScopedReads.ts` العقدين `patients.read` و`orders.read`، لكنه يضبط `DIRECT_REST_SCOPED_READS_BLOCKED = true` لأن استدعاء `/authz/check` من المتصفح وحده لا يفرض القرار على الخادم. إزالة هذا الحاجز الآن ستوصل واجهة NIAM إلى endpoints تعتمد على `LabUser` و`lab_id` فقط، وهو unsafe compatibility bridge وقد يسمح بخلط account/session/workspace models.

> **القرار:** لا يتم تفعيل القراءة السريرية في frontend-v3 حتى يُضاف gateway خادمي حقيقي يشتق actor/workspace/facility من الجلسة، يطبق AuthorizationDecisionService، يفرض tenant/resource scope داخل query، ويسجل audit. لا تُستخدم بيانات mock أو fallback إلى frontend-v2 لتغطية الفجوة.

## فجوات محددة للإصلاح اللاحق

| الأولوية | الفجوة | الإجراء المطلوب | الحالة |
|---|---|---|---|
| P0 | frontend-v3 لا يملك عقد NIAM مثبتًا لقراءة المرضى/الطلبات | تصميم وتنفيذ gateway خادمي versioned فوق الخدمات الحالية أو عقد جديد مع NiamActor وquery-level scope | DECISION_REQUIRED / لا يُنفذ تخمينيًا |
| P1 | frontend-v3 capability UX كان fail-open عند فراغ reflected permissions | توحيد helper fail-closed في `usePermissions` و`Sidebar` مع backend كـenforcement | **تم الإصلاح في Phase 10** |
| P1 | v2 route registry يعتمد outer session gate لمعظم الشاشات | إبقاء v2 legacy، وإدارة كل مسار عبر `LegacyRouteBridge` أو إثبات contract parity قبل التفعيل | PARTIAL |
| P1 | QC direct API surface غير مصنف | إبقاء client read barrier وerror state؛ إضافة عقد خادمي أو تحويل الصفحة إلى safe bridge بعد قرار المنتج | BLOCKED_SAFE |
| P2 | mobile/desktop parity | تشغيل Flutter/Android/iOS toolchains في CI وتأكيد auth/membership/role/workspace contracts | UNVERIFIED |

## النتيجة

لا توجد في هذه المرحلة دعوى بأن كل شاشة مكتملة. تم إثبات أن المسارات المسجلة محمية على مستوى shell، وأن عدة واجهات سريرية محجوبة عمدًا عندما لا يثبت العقد الخادمي المطلوب. وهذا يحقق قاعدة عدم fake functionality، لكنه يترك functional parity للمرضى والطلبات والنتائج والعينات **غير مكتملة** إلى أن يُعتمد gateway خادمي صحيح.
