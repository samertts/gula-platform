# GULA Command 06 — Workspace, Membership & Authorization Integration

## القرار النهائي

> **AUTHORIZATION_CONTEXT_PARTIAL**

تم تحسين العزل الفعلي لسياق Workspace، لكن لا يجوز إعلان اكتمال التكامل الكامل لأن Delegation وواجهة الإدارة الشاملة للعضويات والمؤسسات والمنشآت والدعوات، وتحقق PostgreSQL/Railway الحي، وتكافؤ Android وiOS وFlutter/Desktop غير مثبتة في هذه الجولة.

لم يتم نشر Production، ولم تعدل قاعدة بيانات Production أو feature flags أو التسجيل العام، ولم يبدأ Command 07.

## ما تم تدقيقه

| العنصر | الحالة | الدليل أو الحد |
|---|---|---|
| Account / NiamActor | COMPLETE بالنسبة لمسار actor الحالي | `get_current_niam_actor` يشتق الحساب والجلسة من access token وsession الفعالة. |
| Membership model | COMPLETE/PARTIAL | يدعم عضويات متعددة وحالات ونطاقات organization/facility/department/unit/workspace، مع خدمات انتقال وتدقيق. |
| Membership lifecycle | PARTIAL | توجد طلبات وموافقات ودعوات وقبول وتعليق وإبطال، لكن إدارة lifecycle الشاملة وواجهة الإدارة ليست مكتملة لكل الكيانات. |
| Organization scope | PARTIAL | التفويض المركزي يفرض membership/permission/policy، لكن بعض إدارة المؤسسة منفصلة عن واجهة context الموحدة. |
| Facility scope | PARTIAL → HARDENED | تم ربط workspace eligibility بـfacility/department في membership بدلاً من ownership/representative وحدهما. |
| Workspace model | COMPLETE/PARTIAL | يوجد Workspace وWorkspaceSessionContext وحالات انتقال وتدقيق للتبديل. |
| Workspace selection | PARTIAL → HARDENED | لم تعد الواجهة تختار أول workspace تلقائياً؛ الاختيار الصريح يرسل إلى الخادم والخادم يعيد context authoritative. |
| Workspace switch | COMPLETE بالنسبة للمسار المثبت | التحقق يتم server-side عبر `list_eligible` ثم إنشاء/تحديث context بإصدار متزايد وتدقيق النجاح/الرفض. |
| Role / Permission | PARTIAL | توجد Role/Permission/RoleAssignment وeffective permissions scoped، ويمنع AuthorizationDecisionService unknown/missing permissions. |
| Entitlement | UNVERIFIED/PARTIAL | لم يثبت عقد مستقل كامل للـentitlement عبر كل المنصات في هذه الجولة. |
| Delegation | MISSING/UNVERIFIED | لم يثبت نموذج ومسار delegation مكتمل يحتوي delegator/delegate/scope/expiry/reason/status. لم يتم اختراع bypass. |
| AuthorizationDecisionService | COMPLETE بالنسبة للضوابط المثبتة | يفشل مغلقاً عند actor/session/membership/scope/permission/policy/audit failure، ويسجل القرارات الحساسة. |
| Audit | PARTIAL/COMPLETE للمسارات المختبرة | membership وworkspace وauthorization denial/allow لها تغطية، لكن مجموعة الأحداث الكاملة المطلوبة في Command 06 لم تثبت كلها. |
| Invitations | PARTIAL | الدعوات single-use عملياً عبر token hash/status/expiry ومقيدة بالنطاق ومدققة، لكن واجهة الإدارة الكاملة غير مكتملة. |
| Revocation | PARTIAL | إبطال membership وsession موجود، لكن سياسة الإبطال الفوري لكل role/workspace/facility change تحتاج تحققاً تشغيلياً end-to-end. |

## الإصلاحات المنفذة

### 1. Workspace eligibility أصبحت Membership-scoped

كان الوصول إلى workspaces المؤسسية يعتمد في `WorkspaceService.list_eligible` على ownership/representative في المؤسسة. تم تغيير ذلك إلى:

- السماح بالـpersonal citizen workspace عندما يكون مملوكاً للحساب ولا يرتبط بمؤسسة؛
- السماح بالـorganization workspace فقط عند وجود Membership فعالة وغير منتهية للحساب؛
- مطابقة organization وfacility وdepartment وworkspace عند توفرها؛
- عدم توسيع unit-scoped membership إلى department أو organization workspace لأن Workspace لا يملك علاقة unit مباشرة؛
- إبقاء حالات workspace المسموح بها `active` و`restricted` كما كانت، مع استمرار رفض switch إلى restricted.

### 2. عدم افتراض Workspace افتراضي في الواجهة

تم تعديل `WorkspaceSelector` حتى لا يختار أول workspace حسب ترتيب الاستجابة. يعرض selector حالة `اختر مساحة العمل`، ولا يتم استدعاء `onActiveWorkspace` أو اعتبار أي workspace نشطاً إلا بعد اختيار صريح ونجاح استجابة الخادم. هذا يمنع استخدام صلاحيات سياق غير موثق عند وجود عدة workspaces أو غياب سياسة auto-select.

### 3. اختبارات العزل

أضيفت اختبارات تثبت أن organization workspace يظهر مع membership فعالة ذات نطاق مطابق، وأن unit membership بلا workspace صريح لا تمنح وصولاً أوسع. كما تم تحديث اختبار الواجهة لإثبات عدم auto-select.

## تدفق التفويض المعتمد

```text
Access Token + Active Session
        ↓
NiamActor
        ↓
Active, Unexpired Membership
        ↓
Organization / Facility / Department / Workspace Scope
        ↓
Scoped RoleAssignment → Effective Permission
        ↓
Policy + Resource Scope + Context
        ↓
ALLOW / DENY + Audit
```

الواجهة ليست حاجزاً أمنياً؛ فهي تعرض النتائج فقط. القرار النهائي وإثبات scope وإجراء mutation تبقى في الخادم.

## نتائج الاختبارات

| الفحص | النتيجة |
|---|---:|
| Workspace/Membership/Authorization focused backend tests | **42 ناجحة** |
| Frontend workspace/API tests | **21 ناجحة** في الجولة المركزة |
| Frontend الرسمية عبر `pnpm test` | **53 ناجحة، 15 ملفاً** |
| Frontend lint | ناجح |
| TypeScript typecheck | ناجح |
| Frontend production build | ناجح |
| Backend suite الكاملة | **2668 ناجحة، 4 متخطاة** |
| Ruff على الملفات المعدلة | ناجح |
| `git diff --check` | ناجح |

تشغيل Vitest الخام دون exclude التقط ملفات Playwright داخل `e2e` وأظهر خطأً متوقعاً من اختلاف runner؛ تم بعد ذلك تشغيل script المشروع الرسمي `pnpm test` الذي يستبعد `e2e/**` ونجح بالكامل. هذا ليس فشلاً في تغييرات Command 06.

## Cross-platform status

| المنصة | الحالة |
|---|---|
| Web/PWA | PARTIAL/IMPLEMENTED للمسارات الحالية: WorkspaceSelector وworkspace API والعقود المختبرة. |
| Android | NOT_BUILT أو UNVERIFIED في هذا المستودع؛ لا توجد أدلة parity كاملة. |
| iOS | NOT_BUILT أو UNVERIFIED في هذا المستودع؛ لا توجد أدلة parity كاملة. |
| Flutter/Desktop | UNVERIFIED؛ لم تُثبت دورة context كاملة. |

## Production verification

تمت مراجعة الحالة محلياً فقط. Production commit وruntime authorization configuration وRailway/live PostgreSQL وmigration state التشغيلية لم تُعتبر ناجحة دون وصول حي موثوق، ولذلك تبقى **UNVERIFIED**. لم يحدث أي تغيير Production أو نشر أو merge تلقائي.

## الفجوات المتبقية والموافقة البشرية المطلوبة

يلزم اعتماد تصميم قبل إكمال Command 06 بالكامل للـDelegation وEntitlement المستقل، وإدارة المؤسسات والمنشآت والأدوار والدعوات، وسياسة الإبطال الفوري عند سحب membership أو role أو facility، ونقاط context للـmobile/desktop. كما يلزم اختبار Staging بقاعدة PostgreSQL وRedis حقيقيين وبيانات synthetic لإثبات race conditions وتعدد workers.

بسبب بقاء هذه الفجوات، لا يبدأ Command 07 تلقائياً.
