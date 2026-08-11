# GULA Citizen Workspace — Architecture

## الغرض

Citizen Workspace هو مساحة العمل المواطنية داخل تطبيق GULA الموحد، وليس تطبيقاً مستقلاً ولا نظام authentication جديداً. يستخدم الحساب الموحد وNIAM وطبقة التفويض المشتركة، ويعرض فقط السياق الذي يثبته الخادم للمستخدم الحالي.

> القاعدة الحاكمة: **واجهة المواطن تختار العرض، لكن الخادم يقرر الهوية والسياق والمورد والحق في القراءة أو الكتابة.**

## الطبقات

| الطبقة | القرار المعتمد | ما هو خارج النطاق |
|---|---|---|
| Account | `niam_accounts` هو الحساب الموحد، مع Wave 3 legacy mapping القابل للعكس | citizen-only account أو login stack جديد |
| Person/Identity | `niam_persons` و`niam_identities` يحملان هوية الشخص وحالة التحقق | نسخ national ID الخام أو كلمة المرور إلى Citizen tables |
| Health ID | مرجع صحي opaque مرتبط بالشخص/المواطن عبر mapping مدقق | استخدام national ID كـpublic identifier أو URL key |
| Patient relationship | علاقة صريحة بين الحساب/الشخص والسجل المريض مع scope/status/expiry/audit | اعتبار phone أو family relation تفويضاً شاملاً |
| Workspace | `citizen` workspace داخل shell المشترك، قابل للتعايش مع clinical/lab/workforce | تطبيق مواطن منفصل أو واجهة admin متخفية |
| Authorization | server-side RBAC + ABAC/resource relationship + consent/delegation | role checks في React كحد أمني |
| Data projections | purpose-specific DTOs، final-only clinical projections، provenance | إعادة كامل patient record إلى العميل |
| Audit | login, verification, linkage, record access, downloads, sharing, consent, delegation, denials | تسجيل national ID أو PHI غير الضروري |
| Offline | encrypted, explicitly cached, stale-labelled, sync/conflict-aware | إظهار بيانات سريرية قديمة بلا last-updated |
| Demo | DB/Redis/secrets/connectors منفصلة وsynthetic/read-only قدر الإمكان | أي اتصال إنتاجي أو login bypass |

## سياق الطلب

يُبنى كل طلب على `AuthenticatedAccountContext` داخلي غير قابل للإنشاء من payload العميل، ويشمل account/person/identity verification level/current workspace/organization/roles/permissions/entitlements/device/session. عند طلب سجل مواطن، يضيف الخادم `PatientRelationshipContext` الذي يثبت owner أو guardian أو delegate أو purpose-specific professional access.

تبديل workspace أو profile لا يكتفي بتغيير state في المتصفح؛ بل يعيد تقييم authorization والسياسات والنطاق والـentitlements، ويمسح أي cache لا يثبت صلاحيته للسياق الجديد.

## تدفق الوصول

```text
HttpOnly session / secure mobile session
        |
        v
NIAM account + identity + perm_version
        |
        v
Current workspace/context resolver
        |
        v
Patient relationship / consent / delegation / emergency policy
        |
        v
Purpose-specific service projection
        |
        v
Audit access decision + minimal response
```

## تدرج التنفيذ

يبدأ التنفيذ بإصلاح P0 في citizen-platform routes ومنع caller-supplied IDs، ثم يثبت relationship contract وHealth ID mapping، وبعدها تُبنى واجهة frontend-v3 typed على contracts حقيقية. لا يُعرض أي module غير مدعوم بعقد API واختبار authorization وaudit.

## قرارات الاحتفاظ والتوافق

تبقى `backend/app/routes/citizen_portal.py` و`backend/app/citizen_platform/` مؤقتاً كمسارات compatibility قابلة للتدقيق. لا تُحذف قبل وجود replacement contract، migration/read-only comparison، negative authorization tests، وrollback. الهاتف أو national-ID hash يمكن أن يظل compatibility evidence في مسار قديم محدود، لكنه لا يُعامل كـcanonical relationship.

## غير قابل للتفاوض

لا backfill أو dual-write أو merge تلقائي في Citizen Wave الأولى. لا يُستخدم AI للتشخيص أو الوصف أو تجاوز القرار السريري. لا يُعلن emergency live integration أو offline clinical safety أو native release قبل تشغيل بواباتها الفعلية.
