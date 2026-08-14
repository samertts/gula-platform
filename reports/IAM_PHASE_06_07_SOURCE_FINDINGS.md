# Findings from attached Phase 6 and Phase 7 specifications

## Attached specifications

الملف الأول هو مواصفات **IAM Phase 7 — Role & Permission Engine**. يطلب إنشاء أو تكييف Role Catalog وPermission Catalog وRole Assignment Engine وRole Scope وRole Lifecycle وPermission Enforcement Foundation، مع الفصل الصريح بين Identity وMembership وRole وPermission وContext، وتأجيل ABAC الكامل إلى Phase 8.

الملف الثاني هو مواصفات **IAM Phase 6 — Membership & Relationship Engine**. يطلب إنشاء أو تكييف العلاقة canonical بين Account وOrganization وFacility وDepartment وUnit وWorkspace وProfessional Context، دون حسابات مكررة، مع invitations/applications/administrative provisioning/verified professional links، وحالات lifecycle، والعزل، والتدقيق، وواجهات Frontend/Mobile حقيقية.

## Non-negotiable constraints extracted

يجب التحقق الفعلي من Phases 0–5 قبل بناء Phase 6 أو 7. لا يجوز الاعتماد على التقارير وحدها، ولا يجوز اعتبار Membership تفويضاً شاملاً أو Role permission list داخل الحساب أو الواجهة. كل authorization decision يجب أن يبقى server-authoritative، وكل mutation يحتاج actor/session/scope validation وaudit.

يجب الحفاظ على GULA كسجل سريري وحيد، وعدم اختراع provider أو government integration، وعدم إنشاء حسابات بديلة. كما يجب أن تبقى الحالات immutable تاريخياً، وأن تستخدم uniqueness/FK/transactions، وأن تكون invitation tokens قصيرة العمر، single-use، revocable، ولا تسجل الأسرار.

## Actual source evidence already discovered

- `backend/app/identity/models/assignment.py` هو جسر scoped assignment قائم بين person/employment وorganization/facility/department، ويحتوي `role_id` كسلسلة نصية؛ لكنه ليس canonical Membership أو RoleAssignment engine مكتمل.
- `backend/app/identity/services/citizen_relationship_service.py` يحتوي workflow محدوداً ومُدققاً لـ`create_pending`, `activate`, و`revoke` مع idempotency، لكنه خاص بمسار legacy user/self/citizen workspace وليس Membership Engine عاماً.
- `backend/app/identity/models/citizen_relationship.py` نموذج علاقات مواطن صريح، وليس بديلاً عن membership العام بين الحساب والمنظمة والمنشأة والمساحة.
- `backend/app/identity/models/policy.py` يحتوي IdentityPolicy عامة، لكن لا توجد نماذج Role/Permission/RoleAssignment canonical في مجلد identity models حسب الجرد الحالي.
- `backend/app/identity/services/authorization_service.py` facade رقيق فوق AssignmentRepository وPolicyRepository وClinicalPolicyEvaluator، ولا يثبت وجود Role/Permission catalog قابل للإنفاذ على كل APIs.
- `frontend-v3/src/permissions/index.ts` يحتوي hardcoded client-side RBAC map باستخدام colon-style permission keys؛ وهذا لا يجوز أن يبقى مصدر القرار authoritative.
- `frontend-v3/src/hooks/usePermissions.ts`, `src/components/auth/RoleGuard.tsx`, و`src/layouts/Sidebar.tsx` مستهلكون لهذا hardcoded role/permission map ويحتاجون migration إلى effective capabilities من Backend للعرض فقط.
- مشروع Mobile موجود تحت `mobile/desktop` كـFlutter desktop مع offline/sync layers، لكن parity مع Membership/Role contracts غير مثبت بعد.

## Missing source portions in attachments

الملف الأول ينتهي أثناء تعداد Audit Events عند `ROLE_DE...`، والملف الثاني ينتهي أثناء جملة `If any regression exis...`. لذلك يجب عدم اختلاق الأقسام الناقصة؛ سيتم تنفيذ المتطلبات المكتملة فقط، وتوثيق الجزء غير المتاح كملاحظة مصدرية.
